# NetReaper GUI - Windows Edition

A fully functional Windows-compatible version of the NetReaper security toolkit GUI with native Windows command support and cross-platform compatibility.

## Features

### Windows-Specific Features
- **Native PowerShell Integration** - Execute PowerShell commands directly
- **Windows Command Support** - Full support for CMD and PowerShell commands
- **Windows Path Handling** - Proper Windows path quoting and handling
- **Windows Network Tools** - Integration with native Windows networking tools:
  - `Test-NetConnection` for connectivity testing
  - `ipconfig` for network configuration
  - `netsh` for WiFi management
  - `netstat` for connection monitoring
  - `arp` for ARP table viewing
  - `route` for routing table management

### Cross-Platform Compatibility
- Automatically detects Windows vs Linux/Unix
- Adapts commands and tools based on platform
- Maintains consistent UI across platforms

### Security Tools Integration
- **Port Scanning** - PowerShell-based port scanning and nmap integration
- **Network Discovery** - ARP scanning, DNS lookups, traceroute
- **Web Scanning** - HTTP requests, SSL testing, web enumeration
- **WiFi Tools** - Windows WiFi profile and network management
- **System Tools** - System information, process listing, firewall status

### GUI Features
- **Cyberpunk Bio-Lab Theme** - Dark, futuristic interface with glowing effects
- **Real-time Command Execution** - Live output streaming
- **Command History** - Track and replay previous commands
- **Target History** - Remember and reuse previous targets
- **Multi-Tab Interface** - Organized by security domain
- **Lite Mode** - Resource-conscious operation mode
- **Configuration Editor** - Built-in config file editor

## Installation

### Prerequisites
- Windows 10/11 (or Linux/macOS for cross-platform use)
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Python
Download and install Python from [python.org](https://www.python.org/downloads/)

Make sure to check "Add Python to PATH" during installation.

### Step 2: Install Dependencies
Open PowerShell or Command Prompt and run:

```powershell
cd path\to\Net.Reaper-rebuild-main
pip install -r requirements_windows.txt
```

### Step 3: Run the GUI
```powershell
python netreaper_gui_windows.py
```

## Usage

### Basic Operations

#### 1. Scanning
- Navigate to the **SCAN** tab
- Enter a target IP address or hostname
- Select a scan type from the dropdown
- Click "Initiate Scan"

**Windows-specific scans:**
- Quick Test (Test-NetConnection) - Fast connectivity check
- Port Scan (PowerShell) - Scan ports 1-1000 using native PowerShell
- Nmap Quick/Full - If nmap is installed

#### 2. Reconnaissance
- Navigate to the **RECON** tab
- Enter a target domain or IP
- Choose from:
  - Network scan (arp -a)
  - DNS lookup (nslookup)
  - Traceroute (tracert)
  - WHOIS lookup
  - Port testing

#### 3. Web Scanning
- Navigate to the **WEB** tab
- Enter a target URL
- Run HTTP requests, SSL tests, or nmap HTTP enumeration

#### 4. WiFi Management (Windows)
- Navigate to the **WIRELESS** tab
- View available networks
- Show saved WiFi profiles
- Display interface information

#### 5. System Tools (Windows Only)
- Navigate to the **TOOLS** tab
- Access system information
- View running processes
- Check network statistics
- Display routing and ARP tables
- Check firewall status

### Advanced Features

#### Command Line Interface
Use the command input at the bottom to run custom commands:
```
Test-NetConnection -ComputerName google.com -Port 443
ipconfig /all
netstat -ano | findstr LISTENING
```

#### Lite Mode
Enable Lite Mode from the toolbar to reduce resource usage during scans.

#### Configuration
Click "Edit config" in the toolbar to customize settings.

#### Command History
- All executed commands appear in the history panel
- Double-click any command to re-run it

## Windows Security Tools

### Native Tools (No Installation Required)
- `Test-NetConnection` - Network connectivity testing
- `ipconfig` - IP configuration
- `netstat` - Network statistics
- `arp` - ARP table
- `route` - Routing table
- `netsh` - Network shell (WiFi, firewall, etc.)
- `nslookup` - DNS lookup
- `tracert` - Trace route
- `systeminfo` - System information
- `tasklist` - Process list

### Optional Third-Party Tools
For enhanced functionality, install these tools:

#### Nmap (Recommended)
Download from: https://nmap.org/download.html
- Port scanning
- Service detection
- OS fingerprinting
- Script scanning

#### Wireshark (Optional)
Download from: https://www.wireshark.org/download.html
- Packet capture
- Protocol analysis

#### Python Security Libraries (Optional)
```powershell
pip install scapy requests beautifulsoup4
```

## Configuration

### Config File Location
Windows: `%APPDATA%\NetReaper\config.conf`
Linux: `~/.netreaper/config.conf`

### Sample Configuration
```ini
# NetReaper Configuration
log_level=INFO
default_timeout=30
max_threads=5
```

## Troubleshooting

### "Tool not found" Error
**Solution:** The tool is not installed or not in PATH. Install the tool or use Windows native alternatives.

### PowerShell Execution Policy Error
**Solution:** Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Permission Denied
**Solution:** Some commands require Administrator privileges. Run the GUI as Administrator:
- Right-click `netreaper_gui_windows.py`
- Select "Run as administrator"

### PyQt6 Import Error
**Solution:** Reinstall PyQt6:
```powershell
pip uninstall PyQt6
pip install PyQt6
```

## Security Considerations

### Legal Notice
**IMPORTANT:** This tool is for authorized security testing only. Unauthorized access to computer systems is illegal.

- Only scan systems you own or have written permission to test
- Respect network policies and terms of service
- Be aware of local laws regarding security testing
- Use responsibly and ethically

### Windows Defender
Windows Defender may flag security tools as potentially unwanted. Add exceptions if needed:
1. Open Windows Security
2. Go to Virus & threat protection
3. Manage settings
4. Add exclusions

### Firewall
Some scans may be blocked by Windows Firewall. Configure exceptions as needed.

## Platform Differences

### Windows vs Linux

| Feature | Windows | Linux |
|---------|---------|-------|
| Shell | PowerShell/CMD | Bash |
| Port Scan | PowerShell script | nmap |
| Network Info | ipconfig | ip/ifconfig |
| WiFi | netsh wlan | iwconfig/iw |
| Process List | tasklist | ps |
| Packet Capture | Limited | Full (tcpdump) |

## Development

### Project Structure
```
netreaper_gui_windows.py    # Main GUI application
requirements_windows.txt     # Python dependencies
README_WINDOWS.md           # This file
```

### Key Components
- `CommandThread` - Asynchronous command execution
- `NetReaperGui` - Main window and orchestration
- `ScanTab` - Port scanning interface
- `ReconTab` - Reconnaissance tools
- `WebTab` - Web scanning tools
- `WirelessTab` - WiFi management
- `ToolsTab` - Windows system tools

### Extending the GUI
To add new tools:

1. Add a button in the appropriate tab
2. Create a method to build the command
3. Call `self.executor(command, description, target)`

Example:
```python
def my_custom_scan(self) -> None:
    target = self.target_field.value()
    if not target:
        return
    cmd = f"nmap -sV {quote(target)}"
    self.executor(cmd, "Custom scan", target=target)
```

## Support

### Issues
Report issues at: https://github.com/Nerds489/NETREAPER/issues

### Documentation
Full documentation: See `docs/` directory in the main repository

## License

Copyright (c) 2025 Nerds489
Licensed under the Apache License, Version 2.0

See LICENSE file for details.

## Acknowledgments

- Original NetReaper CLI by Nerds489
- PyQt6 for the GUI framework
- The security research community

---

**NetReaper Windows Edition** - "Some tools scan. Some tools attack. I do both."

© 2025 Nerds489
