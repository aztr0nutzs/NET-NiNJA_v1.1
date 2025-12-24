# NetReaper GUI Desktop Shortcut Creator
# This script creates a desktop shortcut for easy access to NetReaper GUI

Write-Host "NetReaper GUI - Creating Desktop Shortcut" -ForegroundColor Cyan
Write-Host ""

# Get the current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$guiPath = Join-Path $scriptPath "netreaper_gui_windows.py"
$launcherPath = Join-Path $scriptPath "launch_gui.bat"

# Check if files exist
if (-not (Test-Path $guiPath)) {
    Write-Host "[ERROR] netreaper_gui_windows.py not found in current directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get desktop path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "NetReaper GUI.lnk"

# Create shortcut
try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    
    # Use the batch launcher if it exists, otherwise use python directly
    if (Test-Path $launcherPath) {
        $shortcut.TargetPath = $launcherPath
        $shortcut.WorkingDirectory = $scriptPath
        $shortcut.Description = "NetReaper Security Toolkit GUI"
        $shortcut.IconLocation = "powershell.exe,0"
    } else {
        # Find python executable
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if (-not $pythonPath) {
            Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        $shortcut.TargetPath = $pythonPath
        $shortcut.Arguments = "`"$guiPath`""
        $shortcut.WorkingDirectory = $scriptPath
        $shortcut.Description = "NetReaper Security Toolkit GUI"
        $shortcut.IconLocation = "$pythonPath,0"
    }
    
    $shortcut.Save()
    
    Write-Host "[SUCCESS] Desktop shortcut created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Shortcut location: $shortcutPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can now launch NetReaper GUI from your desktop!" -ForegroundColor Cyan
    
} catch {
    Write-Host "[ERROR] Failed to create shortcut: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
