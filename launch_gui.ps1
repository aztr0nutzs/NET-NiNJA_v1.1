# NetReaper GUI Windows PowerShell Launcher
# This PowerShell script launches the NetReaper GUI on Windows

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║ ███╗   ██╗███████╗████████╗██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗           ║" -ForegroundColor Magenta
Write-Host "║ ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗          ║" -ForegroundColor Magenta
Write-Host "║ ██╔██╗ ██║█████╗     ██║   ██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝          ║" -ForegroundColor Magenta
Write-Host "║ ██║╚██╗██║██╔══╝     ██║   ██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗          ║" -ForegroundColor Magenta
Write-Host "║ ██║ ╚████║███████╗   ██║   ██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║          ║" -ForegroundColor Magenta
Write-Host "║ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝          ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Host "NetReaper GUI - Windows Edition" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if PyQt6 is installed
$pyqt6Check = python -c "import PyQt6" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[WARNING] PyQt6 is not installed" -ForegroundColor Yellow
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    
    python -m pip install -r requirements_windows.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[INFO] Dependencies OK" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Launching NetReaper GUI..." -ForegroundColor Cyan
Write-Host ""

# Launch the GUI
python netreaper_gui_windows.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] GUI exited with error code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
