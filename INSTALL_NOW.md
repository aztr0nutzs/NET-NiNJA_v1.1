# NetReaper Windows GUI - Installation Right Now

Follow these exact steps to install and run NetReaper GUI on Windows.

## Step 1: Check Python Installation (2 minutes)

### 1.1 Open PowerShell or Command Prompt
- Press `Win + R`
- Type `powershell` or `cmd`
- Press Enter

### 1.2 Check if Python is installed
```powershell
python --version
```

**Expected output:** `Python 3.8.x` or higher

**If you see an error:**
- Python is not installed
- Go to Step 2

**If you see a version number:**
- Python is installed
- Skip to Step 3

## Step 2: Install Python (5 minutes)

### 2.1 Download Python
1. Open your web browser
2. Go to: https://www.python.org/downloads/
3. Click the big yellow "Download Python 3.x.x" button
4. Save the installer file

### 2.2 Run the Installer
1. Double-click the downloaded file (e.g., `python-3.12.0-amd64.exe`)
2. **IMPORTANT:** Check the box "Add Python to PATH" at the bottom
3. Click "Install Now"
4. Wait for installation to complete (2-3 minutes)
5. Click "Close"

### 2.3 Verify Installation
Open a NEW PowerShell/CMD window and run:
```powershell
python --version
pip --version
```

Both should show version numbers.

## Step 3: Navigate to NetReaper Directory (1 minute)

### 3.1 Open PowerShell/CMD in the NetReaper folder

**Option A: Using File Explorer**
1. Open File Explorer
2. Navigate to the `Net.Reaper-rebuild-main` folder
3. Click in the address bar at the top
4. Type `powershell` and press Enter

**Option B: Using CD command**
```powershell
cd C:\path\to\Net.Reaper-rebuild-main
```
(Replace with your actual path)

### 3.2 Verify you're in the right folder
```powershell
dir
```

You should see files like:
- `netreaper_gui_windows.py`
- `launch_gui.bat`
- `requirements_windows.txt`

## Step 4: Install Dependencies (2 minutes)

### 4.1 Install PyQt6 and dependencies
```powershell
pip install -r requirements_windows.txt
```

**What you'll see:**
```
Collecting PyQt6>=6.4.0
  Downloading PyQt6-6.x.x-...
Installing collected packages: PyQt6-sip, PyQt6-Qt6, PyQt6
Successfully installed PyQt6-6.x.x ...
```

**If you see errors:**
- Try: `python -m pip install --upgrade pip`
- Then retry: `pip install -r requirements_windows.txt`

### 4.2 Verify installation
```powershell
python -c "import PyQt6; print('PyQt6 installed successfully!')"
```

**Expected output:** `PyQt6 installed successfully!`

## Step 5: Launch the GUI (30 seconds)

### Method 1: Using the Batch Launcher (Easiest)
```powershell
.\launch_gui.bat
```
or just double-click `launch_gui.bat` in File Explorer

### Method 2: Using PowerShell Launcher
```powershell
.\launch_gui.ps1
```

### Method 3: Direct Python Execution
```powershell
python netreaper_gui_windows.py
```

## Step 6: First Run (1 minute)

### 6.1 GUI Window Opens
You should see:
- A dark-themed window with purple/cyan colors
- Title: "NetReaper GUI - Windows"
- Multiple tabs: SCAN, RECON, WEB, WIRELESS, TOOLS
- An animated status bar
- Output log at the bottom

### 6.2 Test the Installation
1. Click the **SCAN** tab
2. Click the **"Scan Networks"** button
3. You should see local IP addresses appear
4. Select an IP from the dropdown
5. Click **"Quick Test (Test-NetConnection)"**
6. Watch the output appear in the log

**Success!** If you see output, everything is working!

## 🎯 Quick Test Commands

Try these to verify everything works:

### Test 1: Network Info
```
Tab: TOOLS
Button: IP Config
Result: Shows your network configuration
```

### Test 2: System Info
```
Tab: TOOLS
Button: System Info
Result: Shows your system details
```

### Test 3: DNS Lookup
```
Tab: RECON
Target: google.com
Button: DNS lookup (nslookup)
Result: Shows DNS information
```

## 🚨 Troubleshooting

### Problem: "Python is not recognized"
**Solution:**
1. Reinstall Python
2. Make sure to check "Add Python to PATH"
3. Restart your computer
4. Try again

### Problem: "pip is not recognized"
**Solution:**
```powershell
python -m ensurepip --upgrade
```

### Problem: "PyQt6 installation failed"
**Solution:**
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing again
pip install PyQt6
```

### Problem: "Access is denied"
**Solution:**
Run PowerShell as Administrator:
1. Press `Win + X`
2. Select "Windows PowerShell (Admin)"
3. Navigate to the folder
4. Run the install command again

### Problem: "GUI window doesn't appear"
**Solution:**
1. Check for error messages in the console
2. Verify PyQt6: `python -c "import PyQt6"`
3. Try running with: `python -v netreaper_gui_windows.py`
4. Check if antivirus is blocking it

### Problem: "Cannot run scripts" (PowerShell)
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📌 Optional: Create Desktop Shortcut

After successful installation:

```powershell
.\create_shortcut.ps1
```

This creates a "NetReaper GUI" icon on your desktop for easy access.

## ✅ Installation Complete!

You should now have:
- ✅ Python installed
- ✅ PyQt6 installed
- ✅ NetReaper GUI running
- ✅ Tested basic functionality

## 🎓 Next Steps

1. Read **README_WINDOWS.md** for full features
2. Try different scan types
3. Explore all tabs
4. Check out **QUICKSTART_WINDOWS.md** for more examples

## 📞 Still Having Issues?

1. Check **README_WINDOWS.md** → Troubleshooting section
2. Check **INSTALL_WINDOWS.md** → Detailed troubleshooting
3. Create an issue on GitHub with:
   - Your Windows version
   - Python version
   - Error messages
   - What you tried

---

**Total Time:** ~10 minutes  
**Difficulty:** Easy  
**Requirements:** Windows 10/11, Internet connection  

© 2025 Nerds489
