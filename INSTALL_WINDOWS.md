# NetReaper GUI - Windows Installation Guide

Quick installation guide for the Windows version of NetReaper GUI.

## Quick Start (3 Steps)

### 1. Install Python
Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

**IMPORTANT:** Check "Add Python to PATH" during installation!

### 2. Install Dependencies
Open PowerShell or Command Prompt in the NetReaper directory:

```powershell
pip install -r requirements_windows.txt
```

### 3. Launch the GUI
Double-click `launch_gui.bat` or run:

```powershell
python netreaper_gui_windows.py
```

## Detailed Installation

### Method 1: Using the Launcher (Recommended)

1. **Download/Clone the Repository**
   ```powershell
   git clone https://github.com/Nerds489/NETREAPER.git
   cd NETREAPER\Net.Reaper-rebuild-main
   ```

2. **Run the Launcher**
   - Double-click `launch_gui.bat`, or
   - Right-click `launch_gui.ps1` → "Run with PowerShell"

   The launcher will:
   - Check for Python
   - Install dependencies automatically
   - Launch the GUI

### Method 2: Manual Installation

1. **Install Python**
   - Download from https://www.python.org/downloads/
   - Run installer
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"

2. **Verify Python Installation**
   ```powershell
   python --version
   pip --version
   ```

3. **Install PyQt6**
   ```powershell
   pip install PyQt6
   ```

4. **Install Optional Dependencies**
   ```powershell
   pip install psutil requests
   ```

5. **Run the GUI**
   ```powershell
   python netreaper_gui_windows.py
   ```

## Troubleshooting

### Python Not Found
**Error:** `'python' is not recognized as an internal or external command`

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX`

### PyQt6 Installation Fails
**Error:** `Could not install PyQt6`

**Solution:**
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing again
pip install PyQt6
```

### Permission Denied
**Error:** `Access is denied`

**Solution:**
- Run PowerShell/CMD as Administrator
- Or install for user only:
  ```powershell
  pip install --user PyQt6
  ```

### PowerShell Execution Policy
**Error:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### GUI Won't Start
**Error:** GUI window doesn't appear

**Solution:**
1. Check for errors in the console
2. Verify PyQt6 installation:
   ```powershell
   python -c "import PyQt6; print('OK')"
   ```
3. Try running with verbose output:
   ```powershell
   python -v netreaper_gui_windows.py
   ```

## Optional Tools

### Nmap (Highly Recommended)
For advanced port scanning:

1. Download from https://nmap.org/download.html
2. Run installer (use default options)
3. Restart the GUI

### Wireshark (Optional)
For packet capture:

1. Download from https://www.wireshark.org/download.html
2. Run installer
3. Install with WinPcap/Npcap

## System Requirements

### Minimum
- Windows 10 or later
- Python 3.8+
- 2 GB RAM
- 100 MB disk space

### Recommended
- Windows 10/11
- Python 3.10+
- 4 GB RAM
- 500 MB disk space (for tools)
- Administrator privileges (for some scans)

## First Run

After installation, the GUI will:

1. Create config directory: `%APPDATA%\NetReaper`
2. Initialize configuration files
3. Display the main interface

### Initial Setup
1. Click "Scan Networks" to detect local IPs
2. Try a quick scan on a local IP
3. Explore the different tabs

## Updating

To update to the latest version:

```powershell
# Pull latest changes
git pull

# Update dependencies
pip install --upgrade -r requirements_windows.txt

# Run the GUI
python netreaper_gui_windows.py
```

## Uninstallation

To remove NetReaper GUI:

1. **Remove Python packages:**
   ```powershell
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
   ```

2. **Delete config directory:**
   ```powershell
   Remove-Item -Recurse -Force "$env:APPDATA\NetReaper"
   ```

3. **Delete repository:**
   ```powershell
   Remove-Item -Recurse -Force "path\to\NETREAPER"
   ```

## Getting Help

### Documentation
- Main README: `README_WINDOWS.md`
- Tool reference: `docs/TOOL_REFERENCE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

### Support
- GitHub Issues: https://github.com/Nerds489/NETREAPER/issues
- Discussions: https://github.com/Nerds489/NETREAPER/discussions

## Next Steps

After installation:

1. Read `README_WINDOWS.md` for usage guide
2. Try the example scans in the SCAN tab
3. Explore the TOOLS tab for Windows utilities
4. Check out the configuration editor

---

**Happy Scanning!** 🔒

Remember: Only scan systems you own or have permission to test.
