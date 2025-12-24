@echo off
REM NetReaper GUI Windows Launcher
REM This batch file launches the NetReaper GUI on Windows

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════════════╗
echo ║ ███╗   ██╗███████╗████████╗██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗           ║
echo ║ ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗          ║
echo ║ ██╔██╗ ██║█████╗     ██║   ██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝          ║
echo ║ ██║╚██╗██║██╔══╝     ██║   ██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗          ║
echo ║ ██║ ╚████║███████╗   ██║   ██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║          ║
echo ║ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝          ║
echo ╚══════════════════════════════════════════════════════════════════════════════════════╝
echo.
echo NetReaper GUI - Windows Edition
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

REM Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] PyQt6 is not installed
    echo Installing dependencies...
    python -m pip install -r requirements_windows.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [INFO] Dependencies OK
echo.
echo [INFO] Launching NetReaper GUI...
echo.

REM Launch the GUI
python netreaper_gui_windows.py

if errorlevel 1 (
    echo.
    echo [ERROR] GUI exited with error code %errorlevel%
    pause
)
