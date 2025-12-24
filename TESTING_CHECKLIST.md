# NetReaper GUI Windows - Testing Checklist

Use this checklist to verify the Windows GUI is working correctly.

## ✅ Pre-Installation Tests

### System Requirements
- [ ] Windows 10 or 11 installed
- [ ] At least 2 GB RAM available
- [ ] 500 MB disk space free
- [ ] Internet connection available

### Python Installation
- [ ] Python 3.8+ installed
- [ ] Python in PATH (`python --version` works)
- [ ] pip installed (`pip --version` works)
- [ ] pip can install packages

## ✅ Installation Tests

### Dependency Installation
- [ ] `pip install -r requirements_windows.txt` succeeds
- [ ] PyQt6 imports successfully: `python -c "import PyQt6"`
- [ ] No error messages during installation
- [ ] All dependencies listed in requirements installed

### File Verification
- [ ] `netreaper_gui_windows.py` exists
- [ ] `launch_gui.bat` exists
- [ ] `launch_gui.ps1` exists
- [ ] `requirements_windows.txt` exists
- [ ] All documentation files present

## ✅ Launch Tests

### GUI Startup
- [ ] `python netreaper_gui_windows.py` launches GUI
- [ ] `launch_gui.bat` launches GUI
- [ ] `launch_gui.ps1` launches GUI
- [ ] GUI window appears within 5 seconds
- [ ] No Python errors in console

### Initial Display
- [ ] Window title shows "NetReaper GUI - Windows"
- [ ] All tabs visible (SCAN, RECON, WEB, WIRELESS, TOOLS)
- [ ] Toolbar buttons present
- [ ] Header shows session ID
- [ ] HUD panel animating
- [ ] Output log visible
- [ ] Command input field present
- [ ] History panel visible

## ✅ UI Component Tests

### Toolbar
- [ ] "Clear log" button works
- [ ] "Stop tasks" button present
- [ ] "Lite mode" toggle works
- [ ] "Edit config" opens editor

### Header
- [ ] Session ID displayed
- [ ] Time updates every second
- [ ] Navigation buttons work
- [ ] Stats update correctly

### HUD Panel
- [ ] Status label visible
- [ ] Bio-Pulse animating
- [ ] Latency counter updating
- [ ] Colors changing smoothly

### Tabs
- [ ] Can switch between tabs
- [ ] Each tab loads correctly
- [ ] Scroll areas work
- [ ] Buttons visible in each tab

## ✅ SCAN Tab Tests

### Target Field
- [ ] Can enter IP address
- [ ] Can enter hostname
- [ ] "Scan Networks" button works
- [ ] Dropdown shows history
- [ ] Can select from dropdown

### Quick Test
- [ ] "Quick Test" button visible
- [ ] Clicking executes Test-NetConnection
- [ ] Output appears in log
- [ ] Command completes successfully
- [ ] Return code displayed

### Port Scan
- [ ] "Port Scan" button visible
- [ ] Clicking executes PowerShell port scan
- [ ] Output streams in real-time
- [ ] Can stop scan mid-execution
- [ ] Results show open ports

### Nmap Integration (if installed)
- [ ] "Nmap Quick" button visible
- [ ] Nmap command executes
- [ ] Output displayed correctly
- [ ] Scan completes successfully

## ✅ RECON Tab Tests

### Network Discovery
- [ ] "Network scan (arp -a)" works
- [ ] ARP table displayed
- [ ] Output formatted correctly

### DNS Lookup
- [ ] Can enter domain name
- [ ] "DNS lookup" executes nslookup
- [ ] DNS results displayed
- [ ] Multiple lookups work

### Traceroute
- [ ] "Traceroute" button works
- [ ] tracert command executes
- [ ] Hops displayed in order
- [ ] Can stop traceroute

## ✅ WEB Tab Tests

### HTTP Request
- [ ] Can enter URL
- [ ] "HTTP Request" executes Invoke-WebRequest
- [ ] Response displayed
- [ ] Headers shown

### SSL Test
- [ ] "SSL Test" button works
- [ ] Test-NetConnection port 443 works
- [ ] SSL status displayed

## ✅ WIRELESS Tab Tests

### Windows WiFi
- [ ] "Show Networks" displays networks
- [ ] "Show Profiles" lists saved profiles
- [ ] "Show Interfaces" shows adapters
- [ ] netsh commands execute correctly

## ✅ TOOLS Tab Tests (Windows Only)

### System Information
- [ ] "System Info" button works
- [ ] systeminfo output displayed
- [ ] All system details shown

### Task List
- [ ] "Task List" executes tasklist
- [ ] Process list displayed
- [ ] Can scroll through processes

### Network Stats
- [ ] "Network Stats" runs netstat
- [ ] Connections displayed
- [ ] PIDs shown

### IP Config
- [ ] "IP Config" runs ipconfig /all
- [ ] Network adapters listed
- [ ] IP addresses shown

### Route Table
- [ ] "Route Table" displays routes
- [ ] Routing information correct

### ARP Table
- [ ] "ARP Table" shows ARP cache
- [ ] MAC addresses displayed

### DNS Cache
- [ ] "DNS Cache" shows resolver cache
- [ ] Cached entries listed

### Firewall Status
- [ ] "Firewall Status" shows firewall state
- [ ] All profiles displayed

## ✅ Command Execution Tests

### Manual Commands
- [ ] Can type command in input field
- [ ] Pressing Enter executes command
- [ ] Output appears in log
- [ ] Multiple commands work
- [ ] Command history saved

### PowerShell Commands
- [ ] `Test-NetConnection google.com` works
- [ ] `ipconfig` works
- [ ] `netstat -ano` works
- [ ] `Get-Process` works
- [ ] Multi-line scripts work

### Error Handling
- [ ] Invalid commands show error
- [ ] Missing tools show warning
- [ ] Errors don't crash GUI
- [ ] Error messages clear

## ✅ Feature Tests

### Target History
- [ ] Targets saved after scan
- [ ] History persists between sessions
- [ ] Can select from history
- [ ] Duplicate targets not added
- [ ] History limited to 20 entries

### Command History
- [ ] Commands appear in history panel
- [ ] Double-click re-runs command
- [ ] History persists in session
- [ ] Can scroll through history

### Lite Mode
- [ ] Toggle enables lite mode
- [ ] HUD shows "LITE MODE"
- [ ] Commands prefixed with env var
- [ ] Toggle disables lite mode

### Configuration Editor
- [ ] "Edit config" opens dialog
- [ ] Can edit config text
- [ ] "Save" button saves changes
- [ ] "Cancel" button discards changes
- [ ] Config file created in correct location

### Stop Tasks
- [ ] "Stop tasks" button works
- [ ] Running commands terminated
- [ ] Multiple tasks stopped
- [ ] Status updated correctly

## ✅ Performance Tests

### Startup Performance
- [ ] GUI launches in < 5 seconds
- [ ] No lag when switching tabs
- [ ] Smooth animations
- [ ] Responsive to clicks

### Command Execution
- [ ] Commands start immediately
- [ ] Output streams in real-time
- [ ] No UI freezing
- [ ] Can run multiple commands

### Memory Usage
- [ ] Initial memory < 200 MB
- [ ] Memory stable during use
- [ ] No memory leaks
- [ ] Garbage collection works

### CPU Usage
- [ ] Idle CPU < 5%
- [ ] Scanning CPU reasonable
- [ ] No CPU spikes
- [ ] Animations smooth

## ✅ Compatibility Tests

### Windows Versions
- [ ] Works on Windows 10
- [ ] Works on Windows 11
- [ ] Works on Windows Server (if applicable)

### Python Versions
- [ ] Works with Python 3.8
- [ ] Works with Python 3.9
- [ ] Works with Python 3.10
- [ ] Works with Python 3.11
- [ ] Works with Python 3.12

### Display Resolutions
- [ ] Works at 1280x720 (minimum)
- [ ] Works at 1920x1080 (recommended)
- [ ] Works at 2560x1440
- [ ] Works at 4K (3840x2160)
- [ ] Scales correctly with DPI

### Administrator Mode
- [ ] Works without admin rights (limited)
- [ ] Works with admin rights (full)
- [ ] UAC prompts handled correctly

## ✅ Integration Tests

### With Nmap
- [ ] Detects nmap installation
- [ ] Nmap commands execute
- [ ] Output parsed correctly
- [ ] All nmap features work

### With PowerShell
- [ ] PowerShell 5.1 works
- [ ] PowerShell 7 works
- [ ] Scripts execute correctly
- [ ] Environment variables work

### With Windows Tools
- [ ] All netsh commands work
- [ ] All ipconfig commands work
- [ ] All netstat commands work
- [ ] All system commands work

## ✅ Error Handling Tests

### Missing Tools
- [ ] Warning shown for missing tools
- [ ] GUI doesn't crash
- [ ] Alternative suggested
- [ ] Can continue using GUI

### Invalid Input
- [ ] Invalid IP shows warning
- [ ] Empty target shows warning
- [ ] Invalid commands handled
- [ ] Errors logged correctly

### Network Errors
- [ ] Timeout handled gracefully
- [ ] Connection refused handled
- [ ] DNS errors shown
- [ ] Network down handled

### Permission Errors
- [ ] UAC prompt shown when needed
- [ ] Access denied handled
- [ ] Privilege errors explained
- [ ] Can retry with admin

## ✅ Documentation Tests

### README Files
- [ ] README_WINDOWS.md complete
- [ ] INSTALL_WINDOWS.md accurate
- [ ] QUICKSTART_WINDOWS.md helpful
- [ ] WINDOWS_FEATURES.md detailed

### Code Documentation
- [ ] Functions documented
- [ ] Classes documented
- [ ] Complex logic explained
- [ ] Examples provided

### User Guidance
- [ ] Error messages clear
- [ ] Tooltips helpful
- [ ] Status messages informative
- [ ] Help accessible

## ✅ Security Tests

### Input Validation
- [ ] Command injection prevented
- [ ] Path traversal blocked
- [ ] Special characters escaped
- [ ] SQL injection N/A (no database)

### Privilege Handling
- [ ] Doesn't request unnecessary privileges
- [ ] Admin operations clearly marked
- [ ] UAC prompts appropriate
- [ ] Privilege escalation safe

### Data Protection
- [ ] No sensitive data logged
- [ ] Config file permissions correct
- [ ] History file secure
- [ ] No credentials stored

## ✅ Cleanup Tests

### Uninstallation
- [ ] Can uninstall PyQt6
- [ ] Can remove config directory
- [ ] Can delete application files
- [ ] No registry entries left

### Temporary Files
- [ ] Temp files cleaned up
- [ ] No orphaned processes
- [ ] Logs rotated correctly
- [ ] Cache cleared properly

## 📊 Test Results Summary

### Pass/Fail Counts
- Total Tests: ___
- Passed: ___
- Failed: ___
- Skipped: ___
- Pass Rate: ___%

### Critical Issues
List any critical issues found:
1. 
2. 
3. 

### Minor Issues
List any minor issues found:
1. 
2. 
3. 

### Recommendations
List any recommendations:
1. 
2. 
3. 

## 📝 Testing Notes

### Test Environment
- **OS:** Windows __ (Build ____)
- **Python:** Version ____
- **PyQt6:** Version ____
- **RAM:** __ GB
- **CPU:** ____
- **Display:** ____x____ @ __ DPI

### Tester Information
- **Name:** ____
- **Date:** ____
- **Duration:** ____ minutes
- **Notes:** ____

### Additional Comments
____

---

## ✅ Sign-Off

- [ ] All critical tests passed
- [ ] All major features working
- [ ] Documentation complete
- [ ] Ready for release

**Tested by:** ________________  
**Date:** ________________  
**Signature:** ________________  

---

**NetReaper Windows Edition Testing Checklist**  
Version 1.0.0  
© 2025 Nerds489
