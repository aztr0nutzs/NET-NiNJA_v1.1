from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CapabilityMatrix:
    platform: str
    is_windows: bool
    is_linux: bool
    is_wsl: bool
    is_admin: bool
    tools: Dict[str, bool] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    reasons: Dict[str, str] = field(default_factory=dict)

    def flag(self, name: str) -> bool:
        return bool(self.feature_flags.get(name, False))

    def reason(self, name: str) -> str:
        return self.reasons.get(name, "")


def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def _has_powershell_cmdlet(cmdlet: str) -> bool:
    if not _has_tool("powershell"):
        return False
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-Command {cmdlet}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def _is_admin_windows() -> bool:
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _is_admin_linux() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def _detect_wsl() -> bool:
    return bool(os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"))


def _detect_wsl_available() -> bool:
    return _has_tool("wsl")


def _detect_npcap() -> bool:
    try:
        result = subprocess.run(
            ["sc", "query", "npcap"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0 and "RUNNING" in result.stdout.upper()
    except Exception:
        return False


def detect_capabilities() -> CapabilityMatrix:
    system = platform.system().lower()
    is_windows = system == "windows"
    is_linux = system == "linux"
    is_wsl = _detect_wsl()
    is_admin = _is_admin_windows() if is_windows else _is_admin_linux()

    tools: Dict[str, bool] = {}
    if is_linux:
        for tool in ("ip", "iw", "nmcli", "ss", "nmap", "arp-scan", "ethtool", "ping"):
            tools[tool] = _has_tool(tool)
    if is_windows:
        for tool in ("ipconfig", "getmac", "route", "netsh", "arp", "netstat", "ping", "powershell", "nmap"):
            tools[tool] = _has_tool(tool)
        tools["wsl"] = _detect_wsl_available()
        tools["npcap"] = _detect_npcap()
        tools["Get-NetAdapter"] = _has_powershell_cmdlet("Get-NetAdapter")
        tools["Get-NetIPAddress"] = _has_powershell_cmdlet("Get-NetIPAddress")
        tools["Get-NetRoute"] = _has_powershell_cmdlet("Get-NetRoute")
        tools["Get-NetTCPConnection"] = _has_powershell_cmdlet("Get-NetTCPConnection")
        tools["Get-NetUDPEndpoint"] = _has_powershell_cmdlet("Get-NetUDPEndpoint")
        tools["Get-NetNeighbor"] = _has_powershell_cmdlet("Get-NetNeighbor")

    feature_flags: Dict[str, bool] = {}
    reasons: Dict[str, str] = {}

    if is_linux:
        feature_flags["can_list_interfaces"] = tools.get("ip", False)
        if not feature_flags["can_list_interfaces"]:
            reasons["can_list_interfaces"] = "Missing tool: ip"

        feature_flags["can_show_routes"] = tools.get("ip", False)
        if not feature_flags["can_show_routes"]:
            reasons["can_show_routes"] = "Missing tool: ip"

        feature_flags["can_list_sockets"] = tools.get("ss", False)
        if not feature_flags["can_list_sockets"]:
            reasons["can_list_sockets"] = "Missing tool: ss"

        feature_flags["can_read_neighbors"] = tools.get("ip", False)
        if not feature_flags["can_read_neighbors"]:
            reasons["can_read_neighbors"] = "Missing tool: ip"

        feature_flags["can_scan_wifi"] = tools.get("nmcli", False) or tools.get("iw", False)
        if not feature_flags["can_scan_wifi"]:
            reasons["can_scan_wifi"] = "Missing tool: nmcli or iw"

        feature_flags["can_host_discovery_quick"] = tools.get("ip", False) or tools.get("ping", False)
        if not feature_flags["can_host_discovery_quick"]:
            reasons["can_host_discovery_quick"] = "Missing tool: ip or ping"

        feature_flags["can_host_discovery_full"] = tools.get("nmap", False)
        if not feature_flags["can_host_discovery_full"]:
            reasons["can_host_discovery_full"] = "Missing tool: nmap"

    if is_windows:
        feature_flags["can_list_interfaces"] = tools.get("Get-NetAdapter", False) or tools.get("ipconfig", False)
        if not feature_flags["can_list_interfaces"]:
            reasons["can_list_interfaces"] = "Missing PowerShell Get-NetAdapter or ipconfig"

        feature_flags["can_show_routes"] = tools.get("Get-NetRoute", False) or tools.get("route", False)
        if not feature_flags["can_show_routes"]:
            reasons["can_show_routes"] = "Missing PowerShell Get-NetRoute or route"

        feature_flags["can_list_sockets"] = tools.get("Get-NetTCPConnection", False) or tools.get("netstat", False)
        if not feature_flags["can_list_sockets"]:
            reasons["can_list_sockets"] = "Missing PowerShell Get-NetTCPConnection or netstat"

        feature_flags["can_read_neighbors"] = tools.get("Get-NetNeighbor", False) or tools.get("arp", False)
        if not feature_flags["can_read_neighbors"]:
            reasons["can_read_neighbors"] = "Missing PowerShell Get-NetNeighbor or arp"

        feature_flags["can_scan_wifi"] = tools.get("netsh", False)
        if not feature_flags["can_scan_wifi"]:
            reasons["can_scan_wifi"] = "Missing tool: netsh"

        feature_flags["can_host_discovery_quick"] = tools.get("arp", False) or tools.get("ping", False)
        if not feature_flags["can_host_discovery_quick"]:
            reasons["can_host_discovery_quick"] = "Missing tool: arp or ping"

        feature_flags["can_host_discovery_full"] = tools.get("nmap", False) or tools.get("wsl", False)
        if not feature_flags["can_host_discovery_full"]:
            reasons["can_host_discovery_full"] = "Missing tool: nmap"

    if not is_admin:
        for flag in ("can_scan_wifi", "can_host_discovery_full"):
            if feature_flags.get(flag, False):
                reasons.setdefault(flag, "Admin privileges recommended for full results")

    return CapabilityMatrix(
        platform=platform.system(),
        is_windows=is_windows,
        is_linux=is_linux,
        is_wsl=is_wsl,
        is_admin=is_admin,
        tools=tools,
        feature_flags=feature_flags,
        reasons=reasons,
    )
