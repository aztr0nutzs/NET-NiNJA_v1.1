from __future__ import annotations

from dataclasses import dataclass, asdict
import shutil
from typing import Dict, List, Literal

SupportLevel = Literal["native", "limited", "unsupported", "external_required"]


@dataclass(frozen=True)
class FeatureDefinition:
    key: str
    support_windows: SupportLevel
    support_linux: SupportLevel
    requires_admin: bool
    requires_tools: List[str]
    windows_notes: str
    linux_notes: str
    recommended_path: str

    def support_for(self, os_key: str) -> SupportLevel:
        if os_key == "windows":
            return self.support_windows
        return self.support_linux

    def notes_for(self, os_key: str) -> str:
        if os_key == "windows":
            return self.windows_notes
        return self.linux_notes


FEATURE_MATRIX: Dict[str, FeatureDefinition] = {
    "wireless.monitor_mode": FeatureDefinition(
        key="wireless.monitor_mode",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["airmon-ng"],
        windows_notes="Monitor mode requires external Linux tooling.",
        linux_notes="Uses airmon-ng to toggle monitor mode.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode support.",
    ),
    "wireless.packet_injection": FeatureDefinition(
        key="wireless.packet_injection",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["aireplay-ng"],
        windows_notes="Packet injection requires external Linux tooling.",
        linux_notes="Uses aireplay-ng for injection.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with injection support.",
    ),
    "wireless.wps_attack": FeatureDefinition(
        key="wireless.wps_attack",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["reaver"],
        windows_notes="WPS attacks require external Linux tooling.",
        linux_notes="Uses reaver for WPS attacks.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode.",
    ),
    "wireless.handshake_capture": FeatureDefinition(
        key="wireless.handshake_capture",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["airodump-ng"],
        windows_notes="Handshake capture requires external Linux tooling.",
        linux_notes="Uses airodump-ng for capture.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode.",
    ),
    "wireless.airodump": FeatureDefinition(
        key="wireless.airodump",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["airodump-ng"],
        windows_notes="Wi-Fi capture requires external Linux tooling.",
        linux_notes="Uses airodump-ng for capture.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode.",
    ),
    "wireless.bettercap": FeatureDefinition(
        key="wireless.bettercap",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["bettercap"],
        windows_notes="Bettercap is Linux-first; Windows requires external tooling.",
        linux_notes="Uses bettercap for capture.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode.",
    ),
    "wireless.wifite": FeatureDefinition(
        key="wireless.wifite",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["wifite"],
        windows_notes="Wifite requires external Linux tooling.",
        linux_notes="Uses wifite for automated attacks.",
        recommended_path="Use WSL2 + USB Wi-Fi adapter with monitor mode.",
    ),
    "wireless.aircrack": FeatureDefinition(
        key="wireless.aircrack",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["aircrack-ng"],
        windows_notes="Aircrack-ng is Linux-first; use external tooling on Windows.",
        linux_notes="Uses aircrack-ng for cracking.",
        recommended_path="Use WSL2 with aircrack-ng installed.",
    ),
    "wireless.hashcat": FeatureDefinition(
        key="wireless.hashcat",
        support_windows="native",
        support_linux="native",
        requires_admin=False,
        requires_tools=["hashcat"],
        windows_notes="Hashcat requires GPU drivers if available.",
        linux_notes="Hashcat requires GPU drivers if available.",
        recommended_path="Install hashcat for your platform.",
    ),
    "wireless.convert_handshake": FeatureDefinition(
        key="wireless.convert_handshake",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["hcxpcapngtool"],
        windows_notes="Conversion tool requires external Linux tooling.",
        linux_notes="Uses hcxpcapngtool for conversion.",
        recommended_path="Use WSL2 with hcxpcapngtool installed.",
    ),
    "web.sqlmap": FeatureDefinition(
        key="web.sqlmap",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["sqlmap"],
        windows_notes="SQLmap is Linux-first; use external tooling on Windows.",
        linux_notes="Uses sqlmap for SQL injection testing.",
        recommended_path="Use WSL2 with sqlmap installed.",
    ),
    "web.nikto": FeatureDefinition(
        key="web.nikto",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["nikto"],
        windows_notes="Nikto is Linux-first; use external tooling on Windows.",
        linux_notes="Uses nikto for web scanning.",
        recommended_path="Use WSL2 with nikto installed.",
    ),
    "web.nuclei": FeatureDefinition(
        key="web.nuclei",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["nuclei"],
        windows_notes="Nuclei is Linux-first; use external tooling on Windows.",
        linux_notes="Uses nuclei for template scanning.",
        recommended_path="Use WSL2 with nuclei installed.",
    ),
    "web.xsstrike": FeatureDefinition(
        key="web.xsstrike",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["xsstrike"],
        windows_notes="XSStrike is Linux-first; use external tooling on Windows.",
        linux_notes="Uses XSStrike for XSS testing.",
        recommended_path="Use WSL2 with xsstrike installed.",
    ),
    "web.commix": FeatureDefinition(
        key="web.commix",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["commix"],
        windows_notes="Commix is Linux-first; use external tooling on Windows.",
        linux_notes="Uses commix for command injection testing.",
        recommended_path="Use WSL2 with commix installed.",
    ),
    "web.gobuster": FeatureDefinition(
        key="web.gobuster",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["gobuster"],
        windows_notes="Gobuster is Linux-first; use external tooling on Windows.",
        linux_notes="Uses gobuster for directory fuzzing.",
        recommended_path="Use WSL2 with gobuster installed.",
    ),
    "web.dirb": FeatureDefinition(
        key="web.dirb",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["dirb"],
        windows_notes="Dirb is Linux-first; use external tooling on Windows.",
        linux_notes="Uses dirb for directory fuzzing.",
        recommended_path="Use WSL2 with dirb installed.",
    ),
    "web.feroxbuster": FeatureDefinition(
        key="web.feroxbuster",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["feroxbuster"],
        windows_notes="Feroxbuster is Linux-first; use external tooling on Windows.",
        linux_notes="Uses feroxbuster for directory fuzzing.",
        recommended_path="Use WSL2 with feroxbuster installed.",
    ),
    "discovery.nmap_full": FeatureDefinition(
        key="discovery.nmap_full",
        support_windows="native",
        support_linux="native",
        requires_admin=True,
        requires_tools=["nmap"],
        windows_notes="Full scans require admin privileges.",
        linux_notes="Full scans require root privileges.",
        recommended_path="Install nmap and run the GUI as admin/root.",
    ),
    "discovery.nmap_standard": FeatureDefinition(
        key="discovery.nmap_standard",
        support_windows="native",
        support_linux="native",
        requires_admin=False,
        requires_tools=["nmap"],
        windows_notes="Requires nmap installed.",
        linux_notes="Requires nmap installed.",
        recommended_path="Install nmap for your platform.",
    ),
    "recon.netdiscover": FeatureDefinition(
        key="recon.netdiscover",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["netdiscover"],
        windows_notes="Netdiscover is Linux-first; use external tooling on Windows.",
        linux_notes="Uses netdiscover for LAN discovery.",
        recommended_path="Use WSL2 with netdiscover installed.",
    ),
    "recon.arp_scan": FeatureDefinition(
        key="recon.arp_scan",
        support_windows="external_required",
        support_linux="native",
        requires_admin=True,
        requires_tools=["arp-scan"],
        windows_notes="ARP scan tool is Linux-first; use external tooling on Windows.",
        linux_notes="Uses arp-scan for LAN discovery.",
        recommended_path="Use WSL2 with arp-scan installed.",
    ),
    "recon.nmap_ping": FeatureDefinition(
        key="recon.nmap_ping",
        support_windows="native",
        support_linux="native",
        requires_admin=False,
        requires_tools=["nmap"],
        windows_notes="Requires nmap installed.",
        linux_notes="Requires nmap installed.",
        recommended_path="Install nmap for your platform.",
    ),
    "recon.dnsenum": FeatureDefinition(
        key="recon.dnsenum",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["dnsenum"],
        windows_notes="dnsenum is Linux-first; use external tooling on Windows.",
        linux_notes="Uses dnsenum for DNS enumeration.",
        recommended_path="Use WSL2 with dnsenum installed.",
    ),
    "recon.dnsrecon": FeatureDefinition(
        key="recon.dnsrecon",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["dnsrecon"],
        windows_notes="dnsrecon is Linux-first; use external tooling on Windows.",
        linux_notes="Uses dnsrecon for DNS enumeration.",
        recommended_path="Use WSL2 with dnsrecon installed.",
    ),
    "recon.sslscan": FeatureDefinition(
        key="recon.sslscan",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["sslscan"],
        windows_notes="sslscan is Linux-first; use external tooling on Windows.",
        linux_notes="Uses sslscan for TLS inspection.",
        recommended_path="Use WSL2 with sslscan installed.",
    ),
    "recon.sslyze": FeatureDefinition(
        key="recon.sslyze",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["sslyze"],
        windows_notes="sslyze is Linux-first; use external tooling on Windows.",
        linux_notes="Uses sslyze for TLS inspection.",
        recommended_path="Use WSL2 with sslyze installed.",
    ),
    "recon.onesixtyone": FeatureDefinition(
        key="recon.onesixtyone",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["onesixtyone"],
        windows_notes="onesixtyone is Linux-first; use external tooling on Windows.",
        linux_notes="Uses onesixtyone for SNMP sweep.",
        recommended_path="Use WSL2 with onesixtyone installed.",
    ),
    "recon.enum4linux": FeatureDefinition(
        key="recon.enum4linux",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["enum4linux"],
        windows_notes="enum4linux is Linux-first; use external tooling on Windows.",
        linux_notes="Uses enum4linux for SMB enumeration.",
        recommended_path="Use WSL2 with enum4linux installed.",
    ),
    "wizard.reaper_mode": FeatureDefinition(
        key="wizard.reaper_mode",
        support_windows="external_required",
        support_linux="native",
        requires_admin=False,
        requires_tools=["netreaper"],
        windows_notes="Wizard flows rely on Linux CLI tooling.",
        linux_notes="Uses netreaper CLI wizard flows.",
        recommended_path="Use WSL2 and run the netreaper CLI there.",
    ),
}


def get_feature_matrix() -> Dict[str, FeatureDefinition]:
    return FEATURE_MATRIX


def serialize_feature_matrix(matrix: Dict[str, FeatureDefinition]) -> Dict[str, dict]:
    return {key: asdict(defn) for key, defn in matrix.items()}


def resolve_feature_support(defn: FeatureDefinition, os_key: str, tools: Dict[str, bool], is_admin: bool) -> Dict[str, object]:
    base_support = defn.support_for(os_key)
    notes = defn.notes_for(os_key)
    reasons: List[str] = []

    if base_support == "unsupported":
        reasons.append(f"Unsupported on {os_key}")
    elif base_support == "external_required":
        reasons.append(f"External/WSL required on {os_key}")

    if defn.requires_admin and not is_admin:
        reasons.append("Requires administrator/root privileges")

    missing_tools: List[str] = []
    for tool in defn.requires_tools:
        if not tools.get(tool, False) and shutil.which(tool) is None:
            missing_tools.append(tool)
    if missing_tools:
        reasons.append(f"Missing tool: {', '.join(missing_tools)}")

    enabled = not reasons
    if base_support in ("unsupported", "external_required"):
        enabled = False

    if enabled:
        effective_support: SupportLevel = base_support
    else:
        effective_support = base_support if base_support in ("unsupported", "external_required") else "unsupported"

    return {
        "base_support": base_support,
        "effective_support": effective_support,
        "enabled": enabled,
        "reason": "; ".join(reasons),
        "requires_admin": defn.requires_admin,
        "requires_tools": list(defn.requires_tools),
        "notes": notes,
        "recommended_path": defn.recommended_path,
        "badge": "WSL/External Required" if base_support == "external_required" else "",
    }
