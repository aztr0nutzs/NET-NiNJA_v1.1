# Changelog Entry - WSL Bridge Mode

## Version X.X.X - [Date]

### 🎉 Major Feature: WSL Bridge Mode

Added **WSL Bridge Mode** as a first-class execution backend, enabling Windows users to access the full Linux security toolset through WSL2.

#### What's New

- **WSL Bridge Provider**: Execute Linux tools from Windows GUI via WSL2
- **Backend Selection**: Choose between Windows Native and WSL Bridge modes
- **WSL Diagnostics**: Comprehensive health checks and setup validation
- **Extended Feature Matrix**: All 30+ features now show WSL support status
- **Wireless Support**: Optional USB Wi-Fi adapter passthrough for wireless attacks

#### Features Unlocked on Windows

When using WSL Bridge Mode, Windows users now have access to:

**Web Application Testing**
- SQLMap (SQL injection)
- Nikto (web scanner)
- Nuclei (template scanner)
- XSStrike (XSS testing)
- Commix (command injection)
- Gobuster, Dirb, Feroxbuster (directory fuzzing)

**Reconnaissance Tools**
- DNS enumeration (dnsenum, dnsrecon)
- SSL/TLS scanning (sslscan, sslyze)
- SNMP sweeping (onesixtyone)
- SMB enumeration (enum4linux)
- Netdiscover, ARP scan

**Wireless Tools** (with USB adapter)
- Monitor mode (airmon-ng)
- Packet injection (aireplay-ng)
- WPS attacks (reaver)
- Handshake capture (airodump-ng)
- Automated attacks (wifite)
- Bettercap
- Password cracking (aircrack-ng)

**Network Scanning**
- Full nmap support
- Host discovery
- Port scanning
- Service detection

#### How to Use

1. **Install WSL2**
   ```powershell
   wsl --install
   ```

2. **Install Tools in WSL**
   ```bash
   wsl -- sudo apt update
   wsl -- sudo apt install -y iproute2 net-tools nmap aircrack-ng sqlmap nikto
   ```

3. **Configure Net.Ninja**
   - Open Settings → Backend
   - Select "WSL Bridge"
   - Click "Test Connection"
   - Save settings

4. **Optional: Wireless Setup**
   - Install usbipd-win
   - Attach USB Wi-Fi adapter
   - See docs/WSL_BRIDGE_MODE.md for details

#### Technical Details

- **New Provider**: `providers/wsl.py` implements BaseProvider interface
- **Safe Execution**: WslRunner utility with timeout and error handling
- **Diagnostics**: `wsl_diagnostics.py` validates WSL setup
- **Feature Gating**: Automatic feature availability based on backend
- **Same Data Models**: No GUI changes required

#### Documentation

- `docs/FEATURE_MATRIX.md` - Feature comparison across backends
- `docs/WSL_BRIDGE_MODE.md` - Complete setup and usage guide
- `WSL_IMPLEMENTATION.md` - Technical architecture
- `WSL_INTEGRATION_GUIDE.md` - Developer integration guide
- `WSL_QUICK_REFERENCE.md` - API and command reference

#### Testing

Run the test suite:
```bash
python test_wsl_bridge.py
```

#### Breaking Changes

None. WSL Bridge Mode is opt-in and doesn't affect existing functionality.

#### Known Limitations

- Requires WSL2 (not WSL1)
- Wireless attacks require USB Wi-Fi adapter with monitor mode support
- Some tools may need sudo in WSL
- Slightly higher latency compared to native Linux (~50-100ms per command)

#### Recommended Wireless Adapters

- Alfa AWUS036ACH (RTL8812AU)
- TP-Link TL-WN722N v1 (AR9271)
- Panda PAU09 (RTL8188EUS)
- Alfa AWUS036NHA (AR9271)

#### Migration Guide

No migration needed. Existing Windows Native mode continues to work as before. Users can switch to WSL Bridge Mode in settings when ready.

#### Performance

- Command overhead: ~50-100ms per WSL call
- Network I/O: Near-native performance
- Disk I/O: Fast for WSL filesystem, slower for /mnt/c/
- CPU: Near-native performance
- Scalability: Handles 256+ host ping sweeps efficiently

#### Security Considerations

- WSL2 runs in isolated VM
- USB passthrough gives direct hardware access
- Some operations require admin privileges
- Legal and ethical use only

#### Credits

Implemented following the provider pattern established in the codebase. Special thanks to the WSL team at Microsoft for making this possible.

#### Related Issues

- Closes #XXX: Add Linux tool support on Windows
- Closes #XXX: Enable wireless attacks on Windows
- Closes #XXX: Support WSL2 backend

#### See Also

- [WSL Documentation](https://learn.microsoft.com/en-us/windows/wsl/)
- [usbipd-win](https://github.com/dorssel/usbipd-win)
- [Aircrack-ng](https://www.aircrack-ng.org/)

---

### Other Changes in This Release

[... other changelog entries ...]
