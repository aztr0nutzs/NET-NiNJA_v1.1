# NetReaper GUI - Windows Quick Start

Get up and running in 5 minutes!

## 🚀 Installation (2 minutes)

### Step 1: Install Python
Download from [python.org](https://www.python.org/downloads/) and install.
✅ **Check "Add Python to PATH"**

### Step 2: Install NetReaper
```powershell
# Download and extract, then:
cd path\to\Net.Reaper-rebuild-main
pip install -r requirements_windows.txt
```

### Step 3: Launch
Double-click `launch_gui.bat` or run:
```powershell
python netreaper_gui_windows.py
```

## 🎯 First Scan (1 minute)

1. Click **"Scan Networks"** button to find local IPs
2. Select an IP from the dropdown
3. Click **"Initiate Scan"**
4. Watch results in the output panel

## 📋 Common Tasks

### Quick Network Test
```
Tab: SCAN
Target: 192.168.1.1
Action: Quick Test (Test-NetConnection)
```

### Port Scan
```
Tab: SCAN
Target: 192.168.1.1
Action: Port Scan (PowerShell)
Result: Shows open ports 1-1000
```

### DNS Lookup
```
Tab: RECON
Target: google.com
Action: DNS lookup (nslookup)
```

### View WiFi Networks
```
Tab: WIRELESS
Action: Show Networks
Result: Lists available WiFi networks
```

### System Information
```
Tab: TOOLS (Windows only)
Action: System Info
Result: Detailed system information
```

## 🔧 Essential Commands

### Windows Native Commands
```powershell
# Test connectivity
Test-NetConnection -ComputerName google.com -Port 443

# View network config
ipconfig /all

# Show active connections
netstat -ano

# View ARP table
arp -a

# Show WiFi networks
netsh wlan show networks

# Display routing table
route print
```

### With Nmap (if installed)
```powershell
# Quick scan
nmap -T4 -F 192.168.1.1

# Full scan
nmap -sS -sV -A 192.168.1.1

# Scan subnet
nmap -sn 192.168.1.0/24
```

## 🎨 GUI Features

### Toolbar Actions
- **Clear log** - Clear output window
- **Stop tasks** - Terminate running commands
- **Lite mode** - Reduce resource usage
- **Edit config** - Open configuration editor

### Tabs
- **SCAN** - Port scanning and network testing
- **RECON** - Network discovery and enumeration
- **WEB** - Web application scanning
- **WIRELESS** - WiFi management (limited on Windows)
- **TOOLS** - Windows system utilities

### Command Input
Type commands directly in the bottom input field:
```
Test-NetConnection google.com
ipconfig
netstat -ano
```

### History Panel
- View all executed commands
- Double-click to re-run
- Automatic command logging

## ⚡ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Execute command in input field |
| `Ctrl+L` | Clear log (when focused) |
| `Ctrl+Tab` | Switch tabs |
| `Ctrl+Q` | Quit application |

## 🛠️ Troubleshooting

### Python Not Found
```powershell
# Check if Python is installed
python --version

# If not found, add to PATH or reinstall
```

### PyQt6 Error
```powershell
# Reinstall PyQt6
pip uninstall PyQt6
pip install PyQt6
```

### Permission Denied
```powershell
# Run as Administrator
# Right-click launch_gui.bat → "Run as administrator"
```

### Tool Not Found
```powershell
# Check if tool is installed
where nmap

# Install via Chocolatey
choco install nmap
```

## 📚 Learning Path

### Beginner (Day 1)
1. ✅ Install and launch GUI
2. ✅ Run quick network test
3. ✅ Scan local network
4. ✅ View system information

### Intermediate (Week 1)
1. ✅ Install Nmap
2. ✅ Perform port scans
3. ✅ Use DNS enumeration
4. ✅ Explore web scanning

### Advanced (Month 1)
1. ✅ Install WSL for Linux tools
2. ✅ Create custom scan profiles
3. ✅ Automate scanning tasks
4. ✅ Generate reports

## 🎓 Resources

### Documentation
- **Full Guide:** README_WINDOWS.md
- **Installation:** INSTALL_WINDOWS.md
- **Features:** WINDOWS_FEATURES.md

### External Resources
- **Nmap Tutorial:** https://nmap.org/book/
- **PowerShell Guide:** https://docs.microsoft.com/powershell/
- **Network Security:** https://www.offensive-security.com/

### Community
- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share tips
- **Wiki:** Community-contributed guides

## 💡 Pro Tips

### 1. Use Target History
The GUI remembers your previous targets. Just select from the dropdown!

### 2. Enable Lite Mode
For slower systems, enable Lite Mode to reduce resource usage.

### 3. Save Command History
Commands are automatically saved. Double-click to re-run!

### 4. Install Nmap
For best results, install Nmap from https://nmap.org/download.html

### 5. Run as Administrator
Many scans require admin privileges. Right-click → "Run as administrator"

### 6. Use PowerShell
PowerShell is more powerful than CMD. Use it for better results!

### 7. Create Desktop Shortcut
Run `create_shortcut.ps1` to add a desktop icon.

### 8. Customize Config
Click "Edit config" to customize settings and defaults.

## 🔒 Security Reminders

### Legal Notice
⚠️ **Only scan systems you own or have permission to test!**

### Best Practices
- ✅ Get written authorization
- ✅ Scan during off-hours
- ✅ Document your activities
- ✅ Report findings responsibly
- ❌ Never scan without permission
- ❌ Don't exploit vulnerabilities
- ❌ Don't access unauthorized data

## 🆘 Quick Help

### Command Failed?
1. Check if tool is installed
2. Verify target is reachable
3. Run as Administrator
4. Check firewall settings

### GUI Won't Start?
1. Verify Python installation
2. Check PyQt6 is installed
3. Look for error messages
4. Try reinstalling dependencies

### Slow Performance?
1. Enable Lite Mode
2. Close other applications
3. Disable antivirus temporarily
4. Use faster scan options

## 📞 Getting Support

### Self-Help
1. Check README_WINDOWS.md
2. Search GitHub Issues
3. Review documentation

### Community Support
1. GitHub Discussions
2. Issue Tracker
3. Community Wiki

### Reporting Issues
Include:
- Windows version
- Python version
- Error messages
- Steps to reproduce

---

## Next Steps

Now that you're up and running:

1. 📖 Read the full documentation (README_WINDOWS.md)
2. 🔧 Install optional tools (Nmap, Wireshark)
3. 🎯 Practice on your own network
4. 🚀 Explore advanced features
5. 🤝 Join the community

**Happy Scanning!** 🔒

---

**NetReaper Windows Edition** - "Some tools scan. Some tools attack. I do both."

© 2025 Nerds489
