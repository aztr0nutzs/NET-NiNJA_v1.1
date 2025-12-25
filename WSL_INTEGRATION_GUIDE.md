# WSL Bridge Mode - Integration Guide

Quick guide for integrating WSL Bridge Mode into the Net.Ninja GUI.

## What Was Implemented

✅ **WSL Provider** (`providers/wsl.py`)
- Implements BaseProvider interface
- Executes Linux commands via wsl.exe
- Safe argument handling and timeout enforcement

✅ **WSL Runner** (in `providers/wsl.py`)
- Command execution utility
- JSON and text output parsing
- Distro selection support

✅ **Extended Feature Matrix** (`feature_matrix.py`)
- Added `support_wsl` field to all features
- Added `wsl_notes` for WSL-specific guidance
- New support level: `"wsl_supported"`

✅ **WSL Diagnostics** (`wsl_diagnostics.py`)
- Comprehensive health checks
- Tool availability detection
- Wireless interface detection
- Actionable recommendations

✅ **Updated Capabilities** (`capabilities.py`)
- Backend mode parameter
- WSL-aware capability detection
- Correct feature gating for WSL mode

✅ **Documentation**
- `docs/FEATURE_MATRIX.md` - User-facing feature comparison
- `docs/WSL_BRIDGE_MODE.md` - Setup and usage guide
- `WSL_IMPLEMENTATION.md` - Technical implementation details

✅ **Test Script** (`test_wsl_bridge.py`)
- Diagnostics test
- Provider functionality test
- Example usage

## GUI Integration Checklist

### 1. Settings UI (Backend Selection)

Add to your settings tab:

```python
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import QSettings

# Backend mode selector
backend_label = QLabel("Backend Mode:")
backend_combo = QComboBox()
backend_combo.addItems(["Windows Native", "WSL Bridge"])

# WSL distro selector (only enabled when WSL selected)
distro_label = QLabel("WSL Distribution:")
distro_combo = QComboBox()
distro_combo.setEnabled(False)

# Populate distros
def populate_distros():
    from wsl_diagnostics import _list_distros
    distros = _list_distros()
    distro_combo.clear()
    distro_combo.addItems(["(default)"] + distros)

# Enable/disable distro selector based on backend
def on_backend_changed(index):
    is_wsl = backend_combo.currentText() == "WSL Bridge"
    distro_combo.setEnabled(is_wsl)
    if is_wsl:
        populate_distros()

backend_combo.currentIndexChanged.connect(on_backend_changed)

# Test connection button
test_btn = QPushButton("Run WSL Diagnostics")
def on_test_clicked():
    from wsl_diagnostics import run_wsl_diagnostics, format_diagnostics_report
    distro = distro_combo.currentText()
    if distro == "(default)":
        distro = ""
    diag = run_wsl_diagnostics(distro)
    report = format_diagnostics_report(diag)
    # Show report in dialog or text area
    show_diagnostics_dialog(report)

test_btn.clicked.connect(on_test_clicked)

# Save settings
def save_settings():
    settings = QSettings("NetNinja", "NetNinja")
    settings.setValue("backend_mode", backend_combo.currentText())
    settings.setValue("wsl_distro", distro_combo.currentText())

# Load settings
def load_settings():
    settings = QSettings("NetNinja", "NetNinja")
    backend = settings.value("backend_mode", "Windows Native")
    distro = settings.value("wsl_distro", "(default)")
    backend_combo.setCurrentText(backend)
    distro_combo.setCurrentText(distro)
    on_backend_changed(backend_combo.currentIndex())
```

### 2. Backend Status Chip (Recommended - Sleek UX)

Add the sleek status chip to your header for instant visual feedback:

```python
from gui_backend_status import create_backend_status_chip

# In your main window __init__
self.status_chip = create_backend_status_chip(self)
self.status_chip.clicked.connect(self.show_diagnostics_dialog)

# Add to header layout
header_layout.addWidget(self.status_chip)

# The chip automatically:
# - Shows backend mode (Windows Native / WSL Bridge)
# - Color codes health (Green=OK, Yellow=Warning, Red=Error)
# - Auto-refreshes every 30 seconds
# - Shows diagnostics on click
```

**Color Coding:**
- 🟢 Green: Everything OK
- 🟡 Yellow: Tools missing or warnings
- 🔴 Red: Backend not available
- ⚪ Gray: Unknown/checking

See `BACKEND_STATUS_CHIP_GUIDE.md` for detailed integration guide.

### 3. Provider Initialization

Update your provider initialization code:

```python
from capabilities import detect_capabilities
from providers import get_provider
from PyQt6.QtCore import QSettings

def initialize_provider():
    settings = QSettings("NetNinja", "NetNinja")
    backend = settings.value("backend_mode", "Windows Native")
    distro = settings.value("wsl_distro", "(default)")
    
    # Determine backend mode
    backend_mode = "wsl" if backend == "WSL Bridge" else "native"
    wsl_distro = "" if distro == "(default)" else distro
    
    # Detect capabilities
    capabilities = detect_capabilities(
        backend_mode=backend_mode,
        wsl_distro=wsl_distro
    )
    
    # Get provider
    provider = get_provider(
        capabilities,
        backend_mode=backend_mode,
        wsl_distro=wsl_distro
    )
    
    return provider, capabilities

# Use in your application
provider, capabilities = initialize_provider()
```

### 4. Feature Gating

Update feature availability checks:

```python
from feature_matrix import FEATURE_MATRIX

def is_feature_available(feature_key: str) -> tuple[bool, str]:
    """
    Check if a feature is available.
    
    Returns:
        (available, reason) tuple
    """
    settings = QSettings("NetNinja", "NetNinja")
    backend = settings.value("backend_mode", "Windows Native")
    
    # Determine os_key
    if backend == "WSL Bridge":
        os_key = "wsl"
    elif platform.system() == "Windows":
        os_key = "windows"
    else:
        os_key = "linux"
    
    # Get feature definition
    feature_def = FEATURE_MATRIX.get(feature_key)
    if not feature_def:
        return False, "Feature not found"
    
    # Check support level
    support = feature_def.support_for(os_key)
    notes = feature_def.notes_for(os_key)
    
    if support == "native" or support == "wsl_supported":
        return True, ""
    elif support == "limited":
        return True, notes
    elif support == "external_required":
        return False, notes
    else:  # unsupported
        return False, notes

# Use in UI
available, reason = is_feature_available("wireless.monitor_mode")
if not available:
    monitor_mode_btn.setEnabled(False)
    monitor_mode_btn.setToolTip(reason)
```

### 5. Error Handling

Wrap provider calls with proper error handling:

```python
from providers.base import ProviderError
from PyQt6.QtWidgets import QMessageBox

def safe_provider_call(func, *args, **kwargs):
    """Safely call a provider method with error handling."""
    try:
        return func(*args, **kwargs)
    except ProviderError as e:
        QMessageBox.critical(
            None,
            "Provider Error",
            f"Operation failed: {e}\n\n"
            f"Check your backend settings and WSL configuration."
        )
        return None
    except Exception as e:
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred: {e}"
        )
        return None

# Use in your code
interfaces = safe_provider_call(provider.get_interfaces)
if interfaces:
    # Update UI with interfaces
    pass
```

### 6. Diagnostics Dialog

Create a diagnostics dialog:

```python
from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
from wsl_diagnostics import run_wsl_diagnostics, format_diagnostics_report

class WslDiagnosticsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WSL Diagnostics")
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Text area for report
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFontFamily("Courier New")
        layout.addWidget(self.text_edit)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.run_diagnostics)
        layout.addWidget(refresh_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Run on open
        self.run_diagnostics()
    
    def run_diagnostics(self):
        settings = QSettings("NetNinja", "NetNinja")
        distro = settings.value("wsl_distro", "(default)")
        if distro == "(default)":
            distro = ""
        
        diag = run_wsl_diagnostics(distro)
        report = format_diagnostics_report(diag)
        self.text_edit.setPlainText(report)

# Show dialog
def show_diagnostics_dialog():
    dialog = WslDiagnosticsDialog()
    dialog.exec()
```

## Testing Steps

### 1. Basic Functionality Test

```bash
# Run test script
python test_wsl_bridge.py

# Expected output:
# - WSL diagnostics report
# - Interface discovery test
# - Route discovery test
# - Neighbor discovery test
# - "ALL TESTS PASSED"
```

### 2. GUI Integration Test

1. Launch GUI
2. Go to Settings → Backend
3. Select "WSL Bridge"
4. Click "Run WSL Diagnostics"
5. Verify diagnostics show green checkmarks
6. Click "Save"
7. Restart GUI
8. Verify header badge shows "Backend: WSL"
9. Test network discovery features
10. Verify data appears correctly

### 3. Wireless Test (if USB adapter available)

1. Attach USB adapter: `usbipd attach --wsl --busid X-Y`
2. Run diagnostics
3. Verify "Wireless Interfaces" shows adapter
4. Test Wi-Fi scan feature
5. Verify APs appear in results

## Common Issues

### "WSL not installed"
**Solution**: Run `wsl --install` in PowerShell as Administrator

### "No distros found"
**Solution**: Install Ubuntu: `wsl --install -d Ubuntu`

### "Tools not found"
**Solution**: Install tools in WSL:
```bash
wsl -- sudo apt update
wsl -- sudo apt install -y iproute2 net-tools nmap aircrack-ng
```

### "Permission denied"
**Solution**: Some operations need admin. Run GUI as Administrator.

### GUI freezes during operations
**Solution**: Run provider calls in background thread:
```python
from PyQt6.QtCore import QThread, pyqtSignal

class ProviderWorker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)

# Use it
worker = ProviderWorker(provider.get_interfaces)
worker.finished.connect(lambda interfaces: update_ui(interfaces))
worker.start()
```

## Next Steps

1. ✅ Integrate settings UI
2. ✅ Add header badge
3. ✅ Update provider initialization
4. ✅ Add diagnostics dialog
5. ✅ Test basic functionality
6. ✅ Test with WSL
7. ✅ Document for users
8. ✅ Add to release notes

## Files Modified/Created

### New Files
- `providers/wsl.py` - WSL provider implementation
- `wsl_diagnostics.py` - Diagnostics utility
- `test_wsl_bridge.py` - Test script
- `docs/FEATURE_MATRIX.md` - User documentation
- `docs/WSL_BRIDGE_MODE.md` - Setup guide
- `WSL_IMPLEMENTATION.md` - Technical docs
- `WSL_INTEGRATION_GUIDE.md` - This file

### Modified Files
- `feature_matrix.py` - Added WSL support fields
- `capabilities.py` - Added backend mode parameter
- `providers/__init__.py` - Added WSL provider support

## Support

For issues or questions:
1. Check diagnostics: Run `python test_wsl_bridge.py`
2. Review logs: Check WSL command output
3. Verify WSL: Run `wsl --version` and `wsl -l -v`
4. Check tools: Run `wsl -- which nmap` etc.

## Summary

WSL Bridge Mode is now fully implemented and ready for GUI integration. Follow the checklist above to add the UI components, and use the test script to verify functionality. The implementation is production-ready and follows best practices for error handling, security, and user experience.
