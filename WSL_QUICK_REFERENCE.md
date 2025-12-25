# WSL Bridge Mode - Quick Reference

## For Developers

### Import and Initialize

```python
from capabilities import detect_capabilities
from providers import get_provider
from wsl_diagnostics import run_wsl_diagnostics

# Detect capabilities in WSL mode
capabilities = detect_capabilities(
    backend_mode="wsl",
    wsl_distro="Ubuntu"  # or "" for default
)

# Get WSL provider
provider = get_provider(
    capabilities,
    backend_mode="wsl",
    wsl_distro="Ubuntu"
)

# Run diagnostics
diag = run_wsl_diagnostics("Ubuntu")
if diag.is_ready():
    print("WSL is ready!")
```

### Use Provider

```python
# All methods return same data models as Linux/Windows providers
interfaces = provider.get_interfaces()
routes = provider.get_routes()
sockets = provider.get_sockets()
neighbors = provider.get_neighbors()
wifi_aps = provider.scan_wifi()
hosts = provider.discover_hosts_full("192.168.1.0/24")
```

### Check Feature Support

```python
from feature_matrix import FEATURE_MATRIX

feature = FEATURE_MATRIX["wireless.monitor_mode"]
support = feature.support_for("wsl")  # "wsl_supported"
notes = feature.notes_for("wsl")      # "Requires USB adapter..."
```

### Error Handling

```python
from providers.base import ProviderError

try:
    interfaces = provider.get_interfaces()
except ProviderError as e:
    print(f"WSL command failed: {e}")
```

## For Users

### Quick Setup

```powershell
# 1. Install WSL
wsl --install

# 2. Install tools in WSL
wsl -- sudo apt update
wsl -- sudo apt install -y iproute2 net-tools nmap aircrack-ng

# 3. Configure Net.Ninja
# Settings → Backend → WSL Bridge
```

### Wireless Setup

```powershell
# 1. Install usbipd-win
winget install dorssel.usbipd-win

# 2. Attach USB adapter
usbipd list
usbipd bind --busid 2-3
usbipd attach --wsl --busid 2-3

# 3. Verify in WSL
wsl -- iw dev
```

### Troubleshooting

```bash
# Check WSL
wsl --version
wsl -l -v

# Test distro
wsl -- echo test

# Check tools
wsl -- which nmap
wsl -- which aircrack-ng

# Check wireless
wsl -- iw dev
```

## Feature Support Matrix

| Feature | Windows Native | WSL Bridge | Notes |
|---------|----------------|------------|-------|
| Network Discovery | ✅ | ✅ | Full support |
| Wi-Fi Scan | ⚠️ | ✅ | WSL better |
| Nmap | ✅ | ✅ | Full support |
| Wireless Attacks | ❌ | 🔧 | Needs USB adapter |
| Web Testing | ❌ | ✅ | sqlmap, nikto, etc. |
| Recon Tools | ❌ | ✅ | dnsenum, sslscan, etc. |

Legend:
- ✅ Fully supported
- ⚠️ Limited support
- 🔧 Requires hardware
- ❌ Not supported

## Command Reference

### WSL Commands

```powershell
# List distros
wsl -l -v

# Set default
wsl --set-default Ubuntu

# Run command
wsl -d Ubuntu -- <command>

# Shutdown WSL
wsl --shutdown

# Update WSL
wsl --update
```

### USB Passthrough

```powershell
# List USB devices
usbipd list

# Bind device
usbipd bind --busid 2-3

# Attach to WSL
usbipd attach --wsl --busid 2-3

# Detach
usbipd detach --busid 2-3
```

### Tool Installation

```bash
# Inside WSL
sudo apt update

# Core networking
sudo apt install -y iproute2 net-tools wireless-tools network-manager

# Scanning
sudo apt install -y nmap netdiscover arp-scan

# Wireless
sudo apt install -y aircrack-ng reaver wifite bettercap

# Web testing
sudo apt install -y sqlmap nikto nuclei

# Recon
sudo apt install -y dnsenum dnsrecon sslscan enum4linux
```

## API Reference

### WslRunner

```python
from providers.wsl import WslRunner

runner = WslRunner(distro="Ubuntu", timeout_default=8)

# Execute and parse JSON
data = runner.run_json(["ip", "-j", "addr", "show"])

# Execute and get text
output = runner.run_text(["nmap", "-sn", "192.168.1.0/24"])

# Execute and check success
success = runner.run_check(["which", "nmap"])
```

### WslDiagnostics

```python
from wsl_diagnostics import run_wsl_diagnostics, format_diagnostics_report

diag = run_wsl_diagnostics("Ubuntu")

# Check status
diag.is_ready()           # Basic functionality
diag.is_wireless_ready()  # Wireless capability

# Access results
diag.wsl_installed        # bool
diag.distros              # List[str]
diag.tools_available      # Dict[str, bool]
diag.wireless_interfaces  # List[str]
diag.errors               # List[str]
diag.warnings             # List[str]
diag.recommendations      # List[str]

# Format report
report = format_diagnostics_report(diag)
print(report)
```

### Provider Interface

```python
from providers.base import (
    InterfaceRecord,
    RouteRecord,
    SocketRecord,
    NeighborRecord,
    WifiAPRecord,
    HostRecord,
)

# All providers implement:
class BaseProvider:
    def get_interfaces(self) -> List[InterfaceRecord]: ...
    def get_routes(self) -> List[RouteRecord]: ...
    def get_sockets(self) -> List[SocketRecord]: ...
    def get_neighbors(self) -> List[NeighborRecord]: ...
    def scan_wifi(self) -> List[WifiAPRecord]: ...
    def discover_hosts_quick(self) -> List[HostRecord]: ...
    def discover_hosts_full(self, target: Optional[str]) -> List[HostRecord]: ...
```

## Configuration

### QSettings Keys

```python
from PyQt6.QtCore import QSettings

settings = QSettings("NetNinja", "NetNinja")

# Backend mode
settings.setValue("backend_mode", "WSL Bridge")  # or "Windows Native"

# WSL distro
settings.setValue("wsl_distro", "Ubuntu")  # or "(default)"

# Read
backend = settings.value("backend_mode", "Windows Native")
distro = settings.value("wsl_distro", "(default)")
```

### WSL Config

`C:\Users\<username>\.wslconfig`:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
networkingMode=mirrored
```

## Performance Tips

1. **Store files in WSL**: Faster than `/mnt/c/`
2. **Batch operations**: Combine multiple checks
3. **Use threading**: Don't block GUI
4. **Cache results**: Store distro list, tool availability
5. **Tune timeouts**: Adjust based on operation

## Security Notes

- WSL2 runs in isolated VM
- USB passthrough gives direct hardware access
- Run as admin only when needed
- Be cautious with wireless attacks
- Legal and ethical use only

## Resources

- [WSL Docs](https://learn.microsoft.com/en-us/windows/wsl/)
- [usbipd-win](https://github.com/dorssel/usbipd-win)
- [Feature Matrix](docs/FEATURE_MATRIX.md)
- [Setup Guide](docs/WSL_BRIDGE_MODE.md)
- [Implementation](WSL_IMPLEMENTATION.md)
- [Integration](WSL_INTEGRATION_GUIDE.md)

## Support

Run diagnostics:
```bash
python test_wsl_bridge.py
```

Check WSL:
```powershell
wsl --version
wsl -l -v
wsl -- echo test
```

Verify tools:
```bash
wsl -- which nmap
wsl -- which aircrack-ng
wsl -- iw dev
```
