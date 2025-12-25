"""
Backend Status Chip - Sleek UX component for header
Shows backend mode and health at a glance
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QToolTip
from PyQt6.QtGui import QCursor


class BackendStatus(Enum):
    """Backend health status levels."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class BackendStatusChip(QWidget):
    """
    Sleek status chip for header showing backend mode and health.
    
    Color coding:
    - Green: Everything OK
    - Yellow: Tools missing or warnings
    - Red: Backend not available
    - Gray: Unknown/checking
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._status = BackendStatus.UNKNOWN
        self._backend_mode = "native"
        self._distro = ""
        self._message = ""
        
        # Auto-refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self.refresh_status)
        self._refresh_timer.start(30000)  # Refresh every 30 seconds
        
        # Initial check
        self.refresh_status()
    
    def _setup_ui(self):
        """Setup the chip UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status indicator (colored dot)
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("font-size: 16px; padding: 0 4px;")
        
        # Status text
        self.label = QLabel("Checking...")
        self.label.setStyleSheet("font-weight: bold; padding: 0 8px 0 0;")
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        
        # Make clickable
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click for details")
        
        # Style the chip
        self.setStyleSheet("""
            BackendStatusChip {
                background-color: #f0f0f0;
                border-radius: 12px;
                padding: 4px 8px;
            }
            BackendStatusChip:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle click to show details."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def refresh_status(self):
        """Refresh backend status from settings and diagnostics."""
        settings = QSettings("NetNinja", "NetNinja")
        backend = settings.value("backend_mode", "Windows Native")
        distro = settings.value("wsl_distro", "(default)")
        
        self._backend_mode = "wsl" if backend == "WSL Bridge" else "native"
        self._distro = "" if distro == "(default)" else distro
        
        if self._backend_mode == "native":
            self._check_native_status()
        else:
            self._check_wsl_status()
        
        self._update_ui()
    
    def _check_native_status(self):
        """Check Windows Native backend status."""
        # Windows Native is always OK if we're running
        self._status = BackendStatus.OK
        self._message = "Windows Native: All systems operational"
    
    def _check_wsl_status(self):
        """Check WSL Bridge backend status."""
        try:
            from wsl_diagnostics import run_wsl_diagnostics
            
            diag = run_wsl_diagnostics(self._distro)
            
            if not diag.wsl_installed:
                self._status = BackendStatus.ERROR
                self._message = "WSL not installed"
            elif not diag.selected_distro_exists:
                self._status = BackendStatus.ERROR
                self._message = f"Distro '{self._distro or 'default'}' not found"
            elif not diag.selected_distro_reachable:
                self._status = BackendStatus.ERROR
                self._message = "WSL distro not reachable"
            elif diag.errors:
                self._status = BackendStatus.ERROR
                self._message = diag.errors[0]
            elif diag.warnings:
                self._status = BackendStatus.WARNING
                missing_tools = [tool for tool, avail in diag.tools_available.items() if not avail]
                if missing_tools:
                    self._message = f"Missing tools: {', '.join(missing_tools[:3])}"
                else:
                    self._message = diag.warnings[0]
            else:
                self._status = BackendStatus.OK
                distro_name = self._distro or "default"
                self._message = f"WSL Bridge ({distro_name}): All systems operational"
        
        except Exception as e:
            self._status = BackendStatus.ERROR
            self._message = f"Error checking WSL: {e}"
    
    def _update_ui(self):
        """Update UI based on current status."""
        # Color mapping
        colors = {
            BackendStatus.OK: ("#4CAF50", "#2E7D32"),        # Green
            BackendStatus.WARNING: ("#FF9800", "#F57C00"),   # Orange/Yellow
            BackendStatus.ERROR: ("#F44336", "#C62828"),     # Red
            BackendStatus.UNKNOWN: ("#9E9E9E", "#616161"),   # Gray
        }
        
        color, dark_color = colors[self._status]
        
        # Update indicator color
        self.indicator.setStyleSheet(f"color: {color}; font-size: 16px; padding: 0 4px;")
        
        # Update label text
        if self._backend_mode == "native":
            text = "Windows Native"
        else:
            distro_name = self._distro or "default"
            text = f"WSL ({distro_name})"
        
        # Add status emoji
        if self._status == BackendStatus.OK:
            text = f"✓ {text}"
        elif self._status == BackendStatus.WARNING:
            text = f"⚠ {text}"
        elif self._status == BackendStatus.ERROR:
            text = f"✗ {text}"
        else:
            text = f"? {text}"
        
        self.label.setText(text)
        
        # Update tooltip with detailed message
        tooltip = f"<b>Backend Status</b><br/>{self._message}<br/><br/><i>Click for diagnostics</i>"
        self.setToolTip(tooltip)
        
        # Update chip background color
        self.setStyleSheet(f"""
            BackendStatusChip {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 12px;
                padding: 4px 8px;
            }}
            BackendStatusChip:hover {{
                background-color: {color}30;
                border: 1px solid {color}60;
            }}
        """)
    
    def set_status(self, status: BackendStatus, message: str = ""):
        """Manually set status (for testing or external updates)."""
        self._status = status
        if message:
            self._message = message
        self._update_ui()
    
    def get_status(self) -> BackendStatus:
        """Get current status."""
        return self._status
    
    def get_message(self) -> str:
        """Get current status message."""
        return self._message


# Convenience function for quick integration
def create_backend_status_chip(parent: Optional[QWidget] = None) -> BackendStatusChip:
    """
    Create a backend status chip ready to use.
    
    Usage:
        status_chip = create_backend_status_chip(self)
        status_chip.clicked.connect(self.show_diagnostics_dialog)
        header_layout.addWidget(status_chip)
    
    Returns:
        BackendStatusChip widget
    """
    return BackendStatusChip(parent)


# Example integration code
if __name__ == "__main__":
    """
    Example standalone usage for testing.
    """
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Backend Status Chip Demo")
    
    central = QWidget()
    layout = QVBoxLayout()
    
    # Create status chip
    chip = create_backend_status_chip()
    
    # Add to layout
    layout.addWidget(QLabel("Backend Status:"))
    layout.addWidget(chip)
    layout.addStretch()
    
    # Test buttons
    def show_diagnostics():
        from wsl_diagnostics import run_wsl_diagnostics, format_diagnostics_report
        from PyQt6.QtWidgets import QMessageBox
        
        settings = QSettings("NetNinja", "NetNinja")
        distro = settings.value("wsl_distro", "(default)")
        if distro == "(default)":
            distro = ""
        
        diag = run_wsl_diagnostics(distro)
        report = format_diagnostics_report(diag)
        
        msg = QMessageBox()
        msg.setWindowTitle("WSL Diagnostics")
        msg.setText(report)
        msg.setFont(QFont("Courier New", 9))
        msg.exec()
    
    chip.clicked.connect(show_diagnostics)
    
    # Manual test buttons
    btn_ok = QPushButton("Simulate OK")
    btn_ok.clicked.connect(lambda: chip.set_status(BackendStatus.OK, "All systems operational"))
    layout.addWidget(btn_ok)
    
    btn_warn = QPushButton("Simulate Warning")
    btn_warn.clicked.connect(lambda: chip.set_status(BackendStatus.WARNING, "Missing tools: nmap, aircrack-ng"))
    layout.addWidget(btn_warn)
    
    btn_error = QPushButton("Simulate Error")
    btn_error.clicked.connect(lambda: chip.set_status(BackendStatus.ERROR, "WSL not installed"))
    layout.addWidget(btn_error)
    
    btn_refresh = QPushButton("Refresh Status")
    btn_refresh.clicked.connect(chip.refresh_status)
    layout.addWidget(btn_refresh)
    
    central.setLayout(layout)
    window.setCentralWidget(central)
    window.resize(400, 300)
    window.show()
    
    sys.exit(app.exec())
