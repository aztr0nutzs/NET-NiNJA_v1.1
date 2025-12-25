# WSL Bridge Mode

WSL Bridge Mode allows your Windows GUI to execute Linux-only security tools by running them inside WSL2 and piping results back to the GUI as structured data.

## What is WSL Bridge Mode?

WSL Bridge Mode is a **first-class execution backend** alongside:
- **Linux Native Provider**: Direct Linux execution
- **Windows Native Provider**: PowerShell and Windows tools
- **WSL Bridge Provider**: Windows GUI → WSL2 Linux tools

This is not a fallback mode. It's an explicit choice that unlocks the full Linux security toolset on Windows.

## When to Use WSL Bridge Mode

### ✅ Use WSL Bridge When:
- You're on Windows but need Linux-only tools (sqlmap, nikto, aircrack-ng, etc.)
- You want to run wireless attacks with a USB Wi-Fi adapter
- You need the full penetration testing toolkit
- You want better tool compatibility than Windows native

### ❌ Don't Use WSL Bridge When:
- You're already on Linux (use Linux Native)
- You only need basic network discovery (Windows Native is fine)
- You don't have WSL2 installed

## Quick Setup (No Wireless)

This setup enables all non-wireless features (web testing, recon, nmap, etc.).

### 1. Install WSL2

```powershell
# Run in PowerShell as Administrator
wsl --install
```

This installs WSL2 and Ubuntu by default. Reboot when prompted.

### 2. Install Linux Tools

```bash
# Inside WSL (run: wsl)
sudo apt update
sudo apt install -y \
    iproute2 \
    net-tools \
    wireless-tools \
    network-manager \
    nmap \
    aircrack-ng \
    sqlmap \
    nikto \
    dnsrecon \
    dnsenum \
    sslscan \
    enum4linux
```

### 3. Configure Net.Ninja

1. Open Net.Ninja Settings
2. Set **Backend Mode** to **WSL Bridge**
3. Select your distro (usually `Ubuntu` or leave default)
4. Click **Test Connection**

You're ready! All Linux tools will now work through WSL.

## Wireless Setup (Monitor Mode & Attacks)

For wireless attacks, you need a USB Wi-Fi adapter passed through to WSL.

### Requirements

- **USB Wi-Fi Adapter**: Must support monitor mode on Linux
  - Recommended: Alfa AWUS036ACH, TP-Link TL-WN722N v1, Panda PAU09
- **usbipd-win**: USB passthrough tool for WSL
- **Linux Drivers**: Installed in WSL for your adapter

### 1. Install usbipd-win

Download and install from: https://github.com/dorssel/usbipd-win/releases

Or via winget:
```powershell
winget install --interactive --exact dorssel.usbipd-win
```

### 2. Install USB Tools in WSL

```bash
# Inside WSL
sudo apt update
sudo apt install -y linux-tools-generic hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20
```

### 3. Attach USB Wi-Fi Adapter

```powershell
# In PowerShell as Administrator

# List USB devices
usbipd list

# Find your Wi-Fi adapter (note the BUSID, e.g., 2-3)
# Attach it to WSL
usbipd bind --busid 2-3
usbipd attach --wsl --busid 2-3
```

### 4. Verify in WSL

```bash
# Inside WSL
lsusb  # Should show your adapter
iw dev # Should show wireless interface (e.g., wlan0)
```

If `iw dev` shows your interface, you're ready for wireless attacks!

### 5. Install Wireless Tools

```bash
# Inside WSL
sudo apt install -y \
    aircrack-ng \
    reaver \
    bully \
    wifite \
    bettercap \
    hcxtools \
    hcxdumptool
```

## Troubleshooting

### WSL Not Found
```powershell
# Check WSL installation
wsl --version

# If not installed
wsl --install
```

### Distro Not Reachable
```bash
# Test distro
wsl -d Ubuntu -- echo test

# If fails, try default
wsl -- echo test
```

### Tools Not Found
```bash
# Inside WSL, check tool
which nmap
which aircrack-ng

# Install if missing
sudo apt install nmap aircrack-ng
```

### Wireless Interface Not Visible

**Check USB attachment:**
```powershell
# In PowerShell
usbipd list
# Should show "Attached" status
```

**Check in WSL:**
```bash
lsusb          # Should list adapter
dmesg | tail   # Check for driver errors
iw dev         # Should show interface
```

**Common fixes:**
- Detach and reattach: `usbipd detach --busid 2-3` then `usbipd attach --wsl --busid 2-3`
- Install drivers for your specific adapter
- Try a different USB port
- Ensure adapter supports monitor mode on Linux

### Permission Denied Errors

Some tools need root:
```bash
# Run Net.Ninja GUI as Administrator on Windows
# Or configure sudo without password in WSL (not recommended for production)
```

## WSL Bridge Diagnostics

Net.Ninja includes built-in WSL diagnostics:

1. Open Settings → Backend
2. Click **Run WSL Diagnostics**
3. Review results:
   - WSL installation status
   - Available distros
   - Tool availability
   - Wireless interface detection
   - Actionable recommendations

## What Works Without USB Adapter

These features work in WSL Bridge without any hardware passthrough:

✅ All web application testing (sqlmap, nikto, nuclei, etc.)
✅ DNS enumeration (dnsenum, dnsrecon)
✅ SSL/TLS scanning (sslscan, sslyze)
✅ Network scanning (nmap)
✅ Host discovery
✅ Password cracking (aircrack-ng, hashcat CPU mode)
✅ Handshake conversion tools

## What Requires USB Adapter

These features require a USB Wi-Fi adapter with monitor mode:

🔌 Monitor mode
🔌 Packet injection
🔌 WPS attacks
🔌 Handshake capture (airodump-ng)
🔌 Wireless scanning with injection
🔌 Bettercap wireless features
🔌 Wifite automated attacks

## File and Path Handling

### Wordlists and Config Files

Store wordlists inside WSL for best performance:

```bash
# Inside WSL
mkdir -p ~/.netninja/wordlists
mkdir -p ~/.netninja/config

# Copy from Windows
cp /mnt/c/Users/YourName/Downloads/rockyou.txt ~/.netninja/wordlists/
```

### Accessing Windows Files from WSL

Windows drives are mounted at `/mnt/`:
```bash
# Access C:\Users\YourName\Documents
cd /mnt/c/Users/YourName/Documents
```

### Accessing WSL Files from Windows

Use `\\wsl$\` path:
```
\\wsl$\Ubuntu\home\username\.netninja\
```

## Performance Considerations

- **Network I/O**: Near-native performance
- **Disk I/O**: Faster when files are in WSL filesystem (not `/mnt/c/`)
- **CPU**: Near-native performance
- **GPU**: Limited support (requires WSL-GPU drivers)

## Recommended Adapters for Wireless

| Adapter | Chipset | Monitor Mode | Injection | Notes |
|---------|---------|--------------|-----------|-------|
| Alfa AWUS036ACH | RTL8812AU | ✅ | ✅ | Excellent, widely supported |
| TP-Link TL-WN722N v1 | AR9271 | ✅ | ✅ | Budget option, v1 only! |
| Panda PAU09 | RTL8188EUS | ✅ | ✅ | Good compatibility |
| Alfa AWUS036NHA | AR9271 | ✅ | ✅ | Reliable, older model |

**Important**: Verify the hardware version! Many adapters changed chipsets in v2/v3.

## Security Considerations

- WSL2 runs in a lightweight VM with network isolation
- USB passthrough gives WSL direct hardware access
- Run Net.Ninja as Administrator only when needed
- Be cautious with wireless attacks (legal and ethical use only)

## Limitations

### What WSL Bridge Cannot Do:
- Direct Windows Wi-Fi hardware control (use USB adapter)
- GPU-accelerated hashcat (without WSL-GPU drivers)
- Kernel module loading (some advanced features)
- Raw socket operations (some tools may need root)

### Compared to Native Linux:
- Slightly higher latency for USB devices
- No direct kernel access
- Limited GPU support
- Requires Windows host

## Advanced Configuration

### Multiple Distros

You can install multiple distros and switch between them:

```powershell
# Install additional distro
wsl --install -d Debian

# List distros
wsl -l -v

# Set default
wsl --set-default Debian
```

In Net.Ninja, select the distro from the dropdown.

### WSL Configuration

Create/edit `C:\Users\YourName\.wslconfig`:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

Restart WSL:
```powershell
wsl --shutdown
```

## Getting Help

If you encounter issues:

1. Run **WSL Diagnostics** in Net.Ninja
2. Check `wsl --status` and `wsl --version`
3. Review WSL logs: `wsl --debug-shell`
4. Check tool installation: `which <tool>` in WSL
5. Verify USB attachment: `usbipd list` in PowerShell

## Resources

- [WSL Documentation](https://learn.microsoft.com/en-us/windows/wsl/)
- [USB Passthrough Guide](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)
- [usbipd-win GitHub](https://github.com/dorssel/usbipd-win)
- [Aircrack-ng Documentation](https://www.aircrack-ng.org/)

## Summary

WSL Bridge Mode gives you the best of both worlds:
- Windows GUI and ecosystem
- Full Linux security toolset
- Optional wireless attacks with USB adapter

It's the recommended mode for Windows users who need professional penetration testing capabilities.
