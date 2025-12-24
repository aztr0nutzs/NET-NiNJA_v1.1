# NetReaper GUI - Windows Edition Features

Complete feature list and comparison between Windows and Linux versions.

## Core Features (All Platforms)

### ✅ GUI Framework
- **PyQt6-based Interface** - Modern, responsive GUI
- **Cyberpunk Bio-Lab Theme** - Dark theme with glowing effects
- **Multi-Tab Organization** - Organized by security domain
- **Real-time Output** - Live command execution streaming
- **Command History** - Track and replay commands
- **Target History** - Remember previous targets
- **Session Management** - Unique session IDs and tracking

### ✅ Command Execution
- **Asynchronous Execution** - Non-blocking command execution
- **Thread Management** - Multiple concurrent operations
- **Output Streaming** - Real-time output display
- **Error Handling** - Graceful error recovery
- **Process Control** - Start/stop/terminate operations

### ✅ Configuration
- **Persistent Config** - Save settings between sessions
- **Config Editor** - Built-in configuration editor
- **Lite Mode** - Resource-conscious operation
- **Custom Wordlists** - Select custom wordlist files
- **History Management** - Automatic target history

## Windows-Specific Features

### 🪟 Native Windows Integration

#### PowerShell Support
- **Native PowerShell Execution** - Direct PowerShell command execution
- **PowerShell Quoting** - Proper PowerShell string quoting
- **Environment Variables** - Windows environment variable support
- **PowerShell Scripts** - Multi-line PowerShell script execution

#### Windows Commands
- **CMD Support** - Traditional CMD command execution
- **Batch Scripts** - Execute .bat files
- **Windows Paths** - Proper Windows path handling (backslashes)
- **Drive Letters** - Support for C:\, D:\, etc.

#### Windows Networking
- **Test-NetConnection** - Native connectivity testing
- **ipconfig** - Network configuration
- **netsh** - Network shell commands
- **netstat** - Connection monitoring
- **arp** - ARP table viewing
- **route** - Routing table management
- **tracert** - Windows traceroute

### 🔧 Windows Tools Tab

#### System Information
- **systeminfo** - Detailed system information
- **tasklist** - Running process list
- **Get-Process** - PowerShell process management
- **wmic** - Windows Management Instrumentation

#### Network Diagnostics
- **Network Statistics** - netstat with filtering
- **ARP Table** - View ARP cache
- **DNS Cache** - Display DNS resolver cache
- **Route Table** - View routing information
- **Firewall Status** - Check Windows Firewall state

#### WiFi Management
- **netsh wlan show networks** - Available WiFi networks
- **netsh wlan show profiles** - Saved WiFi profiles
- **netsh wlan show interfaces** - WiFi adapter information
- **netsh wlan export profile** - Export WiFi profiles

### 📁 Windows File System
- **APPDATA Integration** - Config in %APPDATA%\NetReaper
- **TEMP Directory** - Use Windows TEMP folder
- **Path Normalization** - Automatic path conversion
- **UNC Path Support** - Network path support (\\server\share)

### 🚀 Windows Launchers
- **Batch Launcher** - launch_gui.bat for easy startup
- **PowerShell Launcher** - launch_gui.ps1 with checks
- **Desktop Shortcut** - create_shortcut.ps1 for desktop icon
- **Auto-dependency Check** - Automatic PyQt6 installation

## Platform-Specific Scanning

### Windows Scanning Tools

#### Native Scanning
```powershell
# PowerShell Port Scan
1..1000 | ForEach-Object {
    $connection = New-Object System.Net.Sockets.TcpClient
    try {
        $connection.Connect($target, $_)
        Write-Host "Port $_ is open"
    } catch {}
}
```

#### Test-NetConnection
- **Quick Connectivity** - Fast ping and port test
- **Detailed Information** - Route tracing and diagnostics
- **Port Testing** - Test specific ports
- **DNS Resolution** - Automatic name resolution

#### Nmap Integration (Optional)
- **Nmap Quick Scan** - Fast port scanning
- **Nmap Full Scan** - Comprehensive scanning
- **Service Detection** - Identify services
- **OS Fingerprinting** - Detect operating systems

### Linux Scanning Tools

#### Native Tools
- **nmap** - Full nmap suite
- **masscan** - Ultra-fast port scanner
- **rustscan** - Rust-based fast scanner
- **netcat** - Network Swiss Army knife

#### Wireless Tools
- **aircrack-ng** - WiFi security suite
- **airodump-ng** - WiFi packet capture
- **aireplay-ng** - Packet injection
- **airmon-ng** - Monitor mode management
- **reaver** - WPS attacks
- **wifite** - Automated WiFi attacks

## Feature Comparison Matrix

| Feature | Windows | Linux | Notes |
|---------|---------|-------|-------|
| **GUI Framework** | ✅ | ✅ | Identical PyQt6 interface |
| **Port Scanning** | ✅ | ✅ | PowerShell/nmap vs nmap |
| **Network Discovery** | ✅ | ✅ | Different tools, same results |
| **Web Scanning** | ⚠️ | ✅ | Limited without third-party tools |
| **WiFi Scanning** | ⚠️ | ✅ | Basic netsh vs full aircrack-ng |
| **WiFi Attacks** | ❌ | ✅ | Not supported on Windows |
| **Packet Capture** | ⚠️ | ✅ | Limited without Wireshark |
| **System Tools** | ✅ | ✅ | Platform-specific tools |
| **Privilege Escalation** | ✅ | ✅ | UAC vs sudo |
| **Script Execution** | ✅ | ✅ | PowerShell vs Bash |

Legend:
- ✅ Full support
- ⚠️ Limited support
- ❌ Not supported

## Windows Limitations

### 1. Wireless Capabilities
**Limitation:** Windows lacks native monitor mode and packet injection.

**Workaround:**
- Use WSL (Windows Subsystem for Linux) for advanced WiFi testing
- Use external WiFi adapters with monitor mode support
- Use netsh for basic WiFi operations

### 2. Raw Socket Access
**Limitation:** Windows restricts raw socket access.

**Workaround:**
- Run as Administrator
- Use Npcap/WinPcap for packet capture
- Use third-party tools (Wireshark, nmap)

### 3. Tool Availability
**Limitation:** Many Linux security tools don't have Windows versions.

**Workaround:**
- Install Windows versions where available (nmap, Wireshark)
- Use WSL for Linux tools
- Use PowerShell equivalents

### 4. Permission Model
**Limitation:** UAC prompts can interrupt workflows.

**Workaround:**
- Run GUI as Administrator
- Configure UAC settings
- Use scheduled tasks for automation

## Windows Advantages

### 1. Native Integration
- **Windows API Access** - Direct Windows API calls
- **WMI Support** - Windows Management Instrumentation
- **Registry Access** - Read/write Windows Registry
- **Event Logs** - Access Windows Event Viewer

### 2. Enterprise Features
- **Active Directory** - AD enumeration and testing
- **Group Policy** - GPO analysis
- **SCCM Integration** - System Center integration
- **PowerShell Remoting** - Remote management

### 3. GUI Consistency
- **Native Look** - Matches Windows UI guidelines
- **DPI Scaling** - Proper high-DPI support
- **Accessibility** - Windows accessibility features
- **Taskbar Integration** - Windows taskbar support

## Recommended Windows Setup

### Essential Tools
1. **Python 3.10+** - Latest Python version
2. **PyQt6** - GUI framework
3. **Nmap** - Port scanning
4. **Wireshark** - Packet analysis

### Optional Tools
1. **WSL2** - Linux subsystem for advanced tools
2. **Git** - Version control
3. **Visual Studio Code** - Code editing
4. **PowerShell 7** - Latest PowerShell

### Configuration
```powershell
# Install Python packages
pip install PyQt6 psutil requests

# Install Chocolatey (package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install tools via Chocolatey
choco install nmap wireshark git vscode

# Enable WSL2 (optional)
wsl --install
```

## Performance Considerations

### Windows Performance
- **PowerShell Overhead** - Slightly slower than native binaries
- **Antivirus Impact** - Windows Defender may slow scans
- **GUI Responsiveness** - Excellent with PyQt6
- **Memory Usage** - ~100-200 MB typical

### Optimization Tips
1. **Disable Real-time Protection** - For scanning sessions
2. **Use Lite Mode** - Reduce resource usage
3. **Close Background Apps** - Free up resources
4. **Use SSD** - Faster file operations

## Security Considerations

### Windows Security
- **UAC Prompts** - Required for privileged operations
- **Firewall Rules** - May block some scans
- **Antivirus Exclusions** - May need to exclude tools
- **SmartScreen** - May warn about downloaded tools

### Best Practices
1. **Run as Administrator** - For full functionality
2. **Add Exclusions** - Exclude NetReaper directory
3. **Configure Firewall** - Allow necessary ports
4. **Use VPN** - For external scanning

## Future Enhancements

### Planned Features
- [ ] Windows Service Integration
- [ ] Scheduled Scanning
- [ ] Report Generation (PDF/HTML)
- [ ] Database Integration (SQLite)
- [ ] Plugin System
- [ ] Custom Tool Integration
- [ ] Network Mapping Visualization
- [ ] Vulnerability Database Integration

### Community Requests
- [ ] Dark/Light Theme Toggle
- [ ] Custom Keyboard Shortcuts
- [ ] Export Command History
- [ ] Import/Export Configurations
- [ ] Multi-language Support
- [ ] Voice Commands (experimental)

## Contributing

### Windows-Specific Contributions
We welcome contributions for:
- Windows-specific tool integrations
- PowerShell script improvements
- Performance optimizations
- Bug fixes
- Documentation improvements

### Development Setup
```powershell
# Clone repository
git clone https://github.com/Nerds489/NETREAPER.git
cd NETREAPER\Net.Reaper-rebuild-main

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements_windows.txt

# Run in development mode
python netreaper_gui_windows.py
```

## Support

### Getting Help
- **Documentation:** README_WINDOWS.md
- **Installation:** INSTALL_WINDOWS.md
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

### Reporting Bugs
When reporting Windows-specific bugs, include:
- Windows version (Win 10/11)
- Python version
- PyQt6 version
- Error messages
- Steps to reproduce

---

**NetReaper Windows Edition** - Bringing powerful security testing to Windows!

© 2025 Nerds489
