# Feature Matrix

This document provides a comprehensive overview of feature support across different execution backends.

## Backend Modes

Net.Ninja supports three execution backends:

- **Linux Native**: Running directly on Linux with native tools
- **Windows Native**: Running on Windows with PowerShell and Windows tools
- **WSL Bridge**: Running on Windows but executing Linux tools via WSL2

## Legend

- ✅ **Native**: Fully supported with native tools
- ⚠️ **Limited**: Supported with limitations
- 🔧 **WSL Supported**: Supported via WSL Bridge Mode
- ❌ **Unsupported**: Not available on this platform
- 🔌 **External Required**: Requires external tooling or setup

## Core Network Features

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| Interface Discovery | ✅ | ✅ | ✅ | None | Uses `ip` / PowerShell |
| Route Table | ✅ | ✅ | ✅ | None | Uses `ip` / PowerShell |
| Socket Listing | ✅ | ✅ | ✅ | None | Uses `ss` / PowerShell |
| ARP/Neighbor Table | ✅ | ✅ | ✅ | None | Uses `ip neigh` / PowerShell |
| Wi-Fi Scan (Basic) | ✅ | ⚠️ | ✅ | nmcli/netsh | Windows shows APs via netsh |
| Host Discovery (Quick) | ✅ | ✅ | ✅ | None | Uses neighbor table |
| Host Discovery (Full) | ✅ | ✅ | ✅ | nmap (optional) | Nmap recommended |

## Wireless Attack Features

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| Monitor Mode | ✅ | ❌ | 🔧 | airmon-ng, USB adapter | WSL needs USB passthrough |
| Packet Injection | ✅ | ❌ | 🔧 | aireplay-ng, USB adapter | WSL needs USB passthrough |
| WPS Attack | ✅ | ❌ | 🔧 | reaver, USB adapter | WSL needs USB passthrough |
| Handshake Capture | ✅ | ❌ | 🔧 | airodump-ng, USB adapter | WSL needs USB passthrough |
| Airodump-ng | ✅ | ❌ | 🔧 | airodump-ng, USB adapter | WSL needs USB passthrough |
| Bettercap | ✅ | ❌ | 🔧 | bettercap, USB adapter | WSL needs USB passthrough |
| Wifite | ✅ | ❌ | 🔧 | wifite, USB adapter | WSL needs USB passthrough |
| Aircrack-ng | ✅ | 🔌 | ✅ | aircrack-ng | No hardware needed |
| Hashcat | ✅ | ✅ | ⚠️ | hashcat | WSL GPU support limited |
| Handshake Conversion | ✅ | 🔌 | ✅ | hcxpcapngtool | No hardware needed |

## Web Application Testing

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| SQLMap | ✅ | 🔌 | ✅ | sqlmap | Fully supported in WSL |
| Nikto | ✅ | 🔌 | ✅ | nikto | Fully supported in WSL |
| Nuclei | ✅ | 🔌 | ✅ | nuclei | Fully supported in WSL |
| XSStrike | ✅ | 🔌 | ✅ | xsstrike | Fully supported in WSL |
| Commix | ✅ | 🔌 | ✅ | commix | Fully supported in WSL |
| Gobuster | ✅ | 🔌 | ✅ | gobuster | Fully supported in WSL |
| Dirb | ✅ | 🔌 | ✅ | dirb | Fully supported in WSL |
| Feroxbuster | ✅ | 🔌 | ✅ | feroxbuster | Fully supported in WSL |

## Network Scanning & Discovery

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| Nmap (Full Scan) | ✅ | ✅ | ✅ | nmap, admin | Requires admin/root |
| Nmap (Standard) | ✅ | ✅ | ✅ | nmap | No admin required |
| Netdiscover | ✅ | 🔌 | ✅ | netdiscover | Fully supported in WSL |
| ARP Scan | ✅ | 🔌 | ✅ | arp-scan | Fully supported in WSL |
| Nmap Ping Sweep | ✅ | ✅ | ✅ | nmap | Fully supported in WSL |

## Reconnaissance Tools

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| DNS Enum | ✅ | 🔌 | ✅ | dnsenum | Fully supported in WSL |
| DNS Recon | ✅ | 🔌 | ✅ | dnsrecon | Fully supported in WSL |
| SSL Scan | ✅ | 🔌 | ✅ | sslscan | Fully supported in WSL |
| SSLyze | ✅ | 🔌 | ✅ | sslyze | Fully supported in WSL |
| Onesixtyone (SNMP) | ✅ | 🔌 | ✅ | onesixtyone | Fully supported in WSL |
| Enum4linux | ✅ | 🔌 | ✅ | enum4linux | Fully supported in WSL |

## Wizard Modes

| Feature | Linux Native | Windows Native | WSL Bridge | Requirements | Notes |
|---------|--------------|----------------|------------|--------------|-------|
| Reaper Mode | ✅ | 🔌 | ✅ | netreaper CLI | Fully supported in WSL |

## Choosing Your Backend

### Use Linux Native When:
- Running on a Linux system
- Need maximum performance
- Have direct hardware access

### Use Windows Native When:
- Running on Windows
- Only need basic network discovery
- Don't need Linux-specific tools

### Use WSL Bridge When:
- Running on Windows
- Need Linux-only tools (web testing, recon)
- Want wireless attacks (with USB adapter)
- Need the full Linux toolset

## WSL Bridge Wireless Setup

For wireless attacks via WSL Bridge, you need:

1. **USB Wi-Fi Adapter**: Must support monitor mode on Linux
2. **USB Passthrough**: Use `usbipd-win` to attach adapter to WSL
3. **Linux Drivers**: Install appropriate drivers in WSL
4. **Verification**: Run `iw dev` in WSL to confirm interface visibility

See [WSL_BRIDGE_MODE.md](WSL_BRIDGE_MODE.md) for detailed setup instructions.

## Notes

- **Admin/Root Required**: Some features require elevated privileges
- **Tool Installation**: Most tools need to be installed separately
- **Hardware Limitations**: Wireless attacks require compatible hardware
- **WSL2 Required**: WSL Bridge Mode requires WSL2, not WSL1
