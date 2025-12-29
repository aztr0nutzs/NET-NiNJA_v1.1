#!/usr/bin/env python3
"""
IP camera utilities for NetReaper / NET-NiNJA.

Focus:
- ONVIF WS-Discovery (UDP multicast probe) to find cameras on the LAN.
- Lightweight parsing helpers that don't require external ONVIF libraries.
"""

from __future__ import annotations

import socket
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


WS_DISCOVERY_ADDR = ("239.255.255.250", 3702)
SOAP_ENV_NS = "http://www.w3.org/2003/05/soap-envelope"
WSA_NS = "http://schemas.xmlsoap.org/ws/2004/08/addressing"
WSD_NS = "http://schemas.xmlsoap.org/ws/2005/04/discovery"
WSP_NS = "http://schemas.xmlsoap.org/ws/2004/09/policy"
DP_NS = "http://schemas.xmlsoap.org/ws/2006/02/devprof"
DN_NS = "http://www.onvif.org/ver10/network/wsdl"

NS = {
    "s": SOAP_ENV_NS,
    "a": WSA_NS,
    "d": WSD_NS,
    "wsp": WSP_NS,
    "dp": DP_NS,
    "dn": DN_NS,
}

PROBE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="{soap}" xmlns:a="{wsa}" xmlns:d="{wsd}">
  <s:Header>
    <a:Action s:mustUnderstand="1">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>
    <a:MessageID>uuid:{msg_id}</a:MessageID>
    <a:ReplyTo>
      <a:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
    <a:To s:mustUnderstand="1">urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>
  </s:Header>
  <s:Body>
    <d:Probe>
      <d:Types>dn:NetworkVideoTransmitter</d:Types>
    </d:Probe>
  </s:Body>
</s:Envelope>
"""


@dataclass(frozen=True)
class DiscoveredCamera:
    ip: str
    xaddrs: Tuple[str, ...]
    types: Tuple[str, ...] = ()
    scopes: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "ip": self.ip,
            "xaddrs": list(self.xaddrs),
            "types": list(self.types),
            "scopes": list(self.scopes),
        }


def _local_ip_for_multicast() -> str:
    """
    Best-effort local IP to use for multicast traffic.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "0.0.0.0"


def parse_ws_discovery_response(xml_bytes: bytes, sender_ip: str) -> Optional[DiscoveredCamera]:
    """
    Parse a single WS-Discovery ProbeMatch response into a DiscoveredCamera.
    Returns None if the response isn't a ProbeMatch.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    # Find ProbeMatch entries (there can be multiple, but usually one)
    matches = root.findall(".//d:ProbeMatch", NS)
    if not matches:
        return None

    cams: List[DiscoveredCamera] = []
    for match in matches:
        xaddrs = (match.findtext("d:XAddrs", default="", namespaces=NS) or "").split()
        types = (match.findtext("d:Types", default="", namespaces=NS) or "").split()
        scopes = (match.findtext("d:Scopes", default="", namespaces=NS) or "").split()

        # Some devices return empty sender_ip in odd NAT cases; fall back to empty string.
        ip = sender_ip or ""
        if xaddrs:
            cams.append(DiscoveredCamera(ip=ip, xaddrs=tuple(xaddrs), types=tuple(types), scopes=tuple(scopes)))

    if not cams:
        return None

    # Prefer first match; callers can de-dup on ip/xaddrs
    return cams[0]


def ws_discover(timeout_s: float = 1.5, retries: int = 2) -> List[DiscoveredCamera]:
    """
    Broadcast WS-Discovery Probe for ONVIF devices. Returns discovered cameras.

    This is a best-effort scanner and intentionally avoids external ONVIF libs.
    """
    msg_id = str(uuid.uuid4())
    probe = PROBE_TEMPLATE.format(soap=SOAP_ENV_NS, wsa=WSA_NS, wsd=WSD_NS, msg_id=msg_id).encode("utf-8")

    results: Dict[Tuple[str, Tuple[str, ...]], DiscoveredCamera] = {}
    local_ip = _local_ip_for_multicast()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(timeout_s)

        # Bind so we can receive replies; use ephemeral port.
        sock.bind((local_ip, 0))

        for _ in range(max(1, retries)):
            try:
                sock.sendto(probe, WS_DISCOVERY_ADDR)
            except OSError:
                # If send fails, don't loop forever.
                break

            deadline = time.time() + timeout_s
            while time.time() < deadline:
                try:
                    data, (ip, _port) = sock.recvfrom(65535)
                except socket.timeout:
                    break
                except OSError:
                    break

                cam = parse_ws_discovery_response(data, ip)
                if cam is None:
                    continue
                key = (cam.ip, cam.xaddrs)
                results[key] = cam

    finally:
        try:
            sock.close()
        except Exception:
            pass

    return sorted(results.values(), key=lambda c: (c.ip, c.xaddrs))


def guess_rtsp_urls(ip: str, username: str = "", password: str = "", port: int = 554) -> List[str]:
    """
    Provide a shortlist of common RTSP URL patterns. This is just a helper; it does NOT
    replace proper ONVIF media profile discovery.
    """
    auth = ""
    if username and password:
        auth = f"{username}:{password}@"
    elif username:
        auth = f"{username}@"

    base = f"rtsp://{auth}{ip}:{port}"

    candidates = [
        f"{base}/stream1",
        f"{base}/live",
        f"{base}/h264",
        f"{base}/videoMain",
        f"{base}/cam/realmonitor?channel=1&subtype=0",
        f"{base}/cam/realmonitor?channel=1&subtype=1",
        f"{base}/axis-media/media.amp",
        f"{base}/Streaming/Channels/101",
        f"{base}/Streaming/Channels/102",
    ]
    # De-dup, preserve order.
    seen: Set[str] = set()
    out: List[str] = []
    for u in candidates:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out
