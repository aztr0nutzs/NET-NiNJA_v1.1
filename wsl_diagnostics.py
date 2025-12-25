from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WslDiagnostics:
    """WSL Bridge Mode diagnostics results."""
    
    wsl_installed: bool = False
    wsl_version: str = ""
    distros: List[str] = field(default_factory=list)
    default_distro: str = ""
    selected_distro_exists: bool = False
    selected_distro_reachable: bool = False
    
    # Tool availability in WSL
    tools_available: Dict[str, bool] = field(default_factory=dict)
    
    # Wireless interface checks
    wireless_interfaces: List[str] = field(default_factory=list)
    wireless_capable: bool = False
    
    # Diagnostic messages
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def is_ready(self) -> bool:
        """Check if WSL is ready for basic use."""
        return (
            self.wsl_installed
            and self.selected_distro_exists
            and self.selected_distro_reachable
            and not self.errors
        )
    
    def is_wireless_ready(self) -> bool:
        """Check if WSL is ready for wireless operations."""
        return self.is_ready() and self.wireless_capable


def run_wsl_diagnostics(distro: str = "") -> WslDiagnostics:
    """
    Run comprehensive WSL diagnostics.
    
    Args:
        distro: Specific distro to check, or empty for default
    
    Returns:
        WslDiagnostics object with results
    """
    diag = WslDiagnostics()
    
    # Check if wsl.exe is available
    diag.wsl_installed = _check_wsl_installed()
    if not diag.wsl_installed:
        diag.errors.append("WSL is not installed or not in PATH")
        diag.recommendations.append("Install WSL2: wsl --install")
        return diag
    
    # Get WSL version
    diag.wsl_version = _get_wsl_version()
    
    # List available distros
    diag.distros = _list_distros()
    if not diag.distros:
        diag.errors.append("No WSL distributions installed")
        diag.recommendations.append("Install a Linux distribution: wsl --install -d Ubuntu")
        return diag
    
    # Get default distro
    diag.default_distro = _get_default_distro()
    
    # Determine which distro to check
    target_distro = distro or diag.default_distro
    
    # Check if selected distro exists
    diag.selected_distro_exists = target_distro in diag.distros
    if not diag.selected_distro_exists:
        diag.errors.append(f"Selected distro '{target_distro}' not found")
        diag.recommendations.append(f"Available distros: {', '.join(diag.distros)}")
        return diag
    
    # Check if distro is reachable
    diag.selected_distro_reachable = _check_distro_reachable(target_distro)
    if not diag.selected_distro_reachable:
        diag.errors.append(f"Cannot reach distro '{target_distro}'")
        diag.recommendations.append(f"Try: wsl -d {target_distro} -- echo test")
        return diag
    
    # Check for required tools
    required_tools = ["ip", "iw", "nmcli", "nmap", "ss", "ping"]
    for tool in required_tools:
        diag.tools_available[tool] = _check_tool_in_wsl(tool, target_distro)
    
    # Add recommendations for missing tools
    missing_tools = [tool for tool, available in diag.tools_available.items() if not available]
    if missing_tools:
        diag.warnings.append(f"Missing tools in WSL: {', '.join(missing_tools)}")
        diag.recommendations.append(
            f"Install missing tools: wsl -d {target_distro} -- sudo apt update && sudo apt install -y iproute2 wireless-tools network-manager nmap"
        )
    
    # Check for wireless interfaces
    diag.wireless_interfaces = _check_wireless_interfaces(target_distro)
    diag.wireless_capable = len(diag.wireless_interfaces) > 0
    
    if not diag.wireless_capable:
        diag.warnings.append("No wireless interfaces detected in WSL")
        diag.recommendations.append(
            "For wireless attacks, attach a USB Wi-Fi adapter to WSL using usbipd-win"
        )
        diag.recommendations.append(
            "Guide: https://learn.microsoft.com/en-us/windows/wsl/connect-usb"
        )
    
    return diag


def _check_wsl_installed() -> bool:
    """Check if wsl.exe is available."""
    try:
        result = subprocess.run(
            ["wsl.exe", "--version"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def _get_wsl_version() -> str:
    """Get WSL version string."""
    try:
        result = subprocess.run(
            ["wsl.exe", "--version"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            # Parse first line for version
            lines = result.stdout.strip().splitlines()
            if lines:
                return lines[0]
    except Exception:
        pass
    return "unknown"


def _list_distros() -> List[str]:
    """List installed WSL distributions."""
    try:
        result = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            # Parse distro names, filter out empty lines
            distros = [
                line.strip().replace("\x00", "")
                for line in result.stdout.splitlines()
                if line.strip()
            ]
            return distros
    except Exception:
        pass
    return []


def _get_default_distro() -> str:
    """Get the default WSL distribution."""
    try:
        result = subprocess.run(
            ["wsl.exe", "-l", "-v"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            # Look for line with asterisk (default)
            for line in result.stdout.splitlines():
                if "*" in line:
                    # Extract distro name
                    parts = line.replace("*", "").split()
                    if parts:
                        return parts[0].replace("\x00", "")
    except Exception:
        pass
    return ""


def _check_distro_reachable(distro: str) -> bool:
    """Check if a distro is reachable."""
    try:
        cmd = ["wsl.exe"]
        if distro:
            cmd.extend(["-d", distro])
        cmd.extend(["--", "echo", "test"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "test" in result.stdout
    except Exception:
        return False


def _check_tool_in_wsl(tool: str, distro: str) -> bool:
    """Check if a tool is available in WSL."""
    try:
        cmd = ["wsl.exe"]
        if distro:
            cmd.extend(["-d", distro])
        cmd.extend(["--", "which", tool])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_wireless_interfaces(distro: str) -> List[str]:
    """Check for wireless interfaces in WSL using iw dev."""
    try:
        cmd = ["wsl.exe"]
        if distro:
            cmd.extend(["-d", distro])
        cmd.extend(["--", "iw", "dev"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        
        if result.returncode != 0:
            return []
        
        # Parse iw dev output for interface names
        interfaces = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Interface "):
                iface = line.split()[1]
                interfaces.append(iface)
        
        return interfaces
    except Exception:
        return []


def format_diagnostics_report(diag: WslDiagnostics) -> str:
    """Format diagnostics as a human-readable report."""
    lines = []
    lines.append("=== WSL Bridge Mode Diagnostics ===\n")
    
    lines.append(f"WSL Installed: {'✓' if diag.wsl_installed else '✗'}")
    if diag.wsl_version:
        lines.append(f"WSL Version: {diag.wsl_version}")
    
    if diag.distros:
        lines.append(f"\nInstalled Distributions: {', '.join(diag.distros)}")
        if diag.default_distro:
            lines.append(f"Default Distro: {diag.default_distro}")
    
    if diag.selected_distro_exists:
        lines.append(f"\nSelected Distro Reachable: {'✓' if diag.selected_distro_reachable else '✗'}")
    
    if diag.tools_available:
        lines.append("\nTool Availability:")
        for tool, available in sorted(diag.tools_available.items()):
            status = "✓" if available else "✗"
            lines.append(f"  {status} {tool}")
    
    if diag.wireless_interfaces:
        lines.append(f"\nWireless Interfaces: {', '.join(diag.wireless_interfaces)}")
    else:
        lines.append("\nWireless Interfaces: None detected")
    
    if diag.errors:
        lines.append("\n❌ Errors:")
        for error in diag.errors:
            lines.append(f"  • {error}")
    
    if diag.warnings:
        lines.append("\n⚠️  Warnings:")
        for warning in diag.warnings:
            lines.append(f"  • {warning}")
    
    if diag.recommendations:
        lines.append("\n💡 Recommendations:")
        for rec in diag.recommendations:
            lines.append(f"  • {rec}")
    
    lines.append(f"\nOverall Status: {'✓ Ready' if diag.is_ready() else '✗ Not Ready'}")
    lines.append(f"Wireless Ready: {'✓ Yes' if diag.is_wireless_ready() else '✗ No'}")
    
    return "\n".join(lines)
