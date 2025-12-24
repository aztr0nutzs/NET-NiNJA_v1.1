#!/usr/bin/env python3
"""
NetReaper GUI — Windows-Compatible Cyberpunk Security Toolkit Interface

A fully functional Windows-compatible version of the NetReaper GUI with:
- Native Windows command execution (PowerShell/CMD)
- Windows path handling
- Windows-specific security tools integration
- Cross-platform compatibility
"""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

import psutil
from uuid import uuid4
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BASE_DIR.parent))

from gui_components import PanelWindow, PanelWorkspacePage
from gui_theme import apply_bio_theme
from security_utils import sanitize_command_for_display

# Windows detection and WSL check
IS_WINDOWS = platform.system() == "Windows"

def is_wsl_available():
    """Check if WSL is installed and available in the system's PATH."""
    return shutil.which("wsl.exe") is not None


def get_config_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), ".netreaper")
    os.makedirs(base, exist_ok=True)
    history_dir = os.path.join(base, "history")
    os.makedirs(history_dir, exist_ok=True)
    return base

class CommandThread(QThread):
    """
    Runs a shell command and emits its output line by line.
    SECURITY: Hardened for Windows, uses process groups and psutil for termination.
    """

    output = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command: Iterable[str] | str, sanitize_output: bool = True):
        super().__init__()
        self.command = command
        self.sanitize_output = sanitize_output
        self.process: Optional[subprocess.Popen] = None

    def _build_argv(self) -> List[str]:
        if isinstance(self.command, (list, tuple)):
            return list(self.command)
        return shlex.split(self.command)

    def run(self) -> None:
        try:
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0
            cmd_args = self._build_argv()

            self.process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
            )
        except (FileNotFoundError, OSError, ValueError) as exc:
            self.output.emit(f"[error] {exc}")
            self.finished.emit(1)
            return

        assert self.process.stdout
        for line in iter(self.process.stdout.readline, ""):
            output_line = line.rstrip()
            if self.sanitize_output:
                output_line = self._sanitize_output(output_line)
            self.output.emit(output_line)
        self.process.stdout.close()
        return_code = self.process.wait()
        self.finished.emit(return_code)

    def _sanitize_output(self, line: str) -> str:
        """Remove sensitive patterns from output to prevent credential leakage."""
        import re
        line = re.sub(r'(password|passwd|pwd)[=:\s]+\S+', r'\1=***REDACTED***', line, flags=re.IGNORECASE)
        line = re.sub(r'(api[_-]?key|token|secret)[=:\s]+\S+', r'\1=***REDACTED***', line, flags=re.IGNORECASE)
        line = re.sub(r'(Authorization|Bearer)[:\s]+\S+', r'\1: ***REDACTED***', line, flags=re.IGNORECASE)
        return line

    def terminate(self) -> None:
        """Reliably terminate the process and its entire child process tree."""
        if not self.process or self.process.poll() is not None:
            return

        try:
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait for children to die
            psutil.wait_procs(children, timeout=3)

            # Terminate the parent process
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass

            self.output.emit("[status] Task terminated.")
        except psutil.NoSuchProcess:
            # Process already finished
            pass
        except Exception as e:
            self.output.emit(f"[error] Failed to terminate process: {e}")
            # Fallback to forceful taskkill if psutil fails
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
            else:
                self.process.kill()

def quote(value: Optional[str]) -> str:
    if value is None:
        return ""
    if IS_WINDOWS:
        # PowerShell quoting: escape single quotes by doubling them up
        return f"'{value.strip().replace(''', ''''')}'"
    return shlex.quote(value.strip())


def apply_glow_effect(widget: QWidget, color: str = "#7c5dff", intensity: int = 25) -> None:
    """Add an intense pulsating electrified glow effect via drop shadow animation."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(intensity)
    effect.setColor(QColor(color))
    effect.setOffset(0, 0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"blurRadius", widget)
    animation.setStartValue(intensity - 10)
    animation.setEndValue(intensity + 25)
    animation.setDuration(1500)
    animation.setLoopCount(-1)
    try:
        animation.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutSine))
    except Exception:
        try:
            animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        except Exception:
            pass
    animation.start()
    widget._glow_animation = animation


def create_glowing_button(text: str, callback, color: str = "#c87bff", enabled=True) -> QPushButton:
    """Create a button with intense electrified glow effect."""
    button = QPushButton(text)
    button.clicked.connect(lambda checked=False, cb=callback: cb())
    button.setMinimumHeight(45)
    button.setEnabled(enabled)
    button.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 {color}80,
                                        stop:1 {color}40);
            border: 2px solid {color};
            border-radius: 8px;
            color: #ffffff;
            font-weight: 700;
            font-size: 14px;
            padding: 12px 24px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 {color}A0,
                                        stop:1 {color}60);
            border: 2px solid {color}FF;
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 {color}60,
                                        stop:1 {color}30);
        }}
        QPushButton:disabled {{
            background: rgba(50, 50, 50, .3);
            border: 2px solid rgba(80, 80, 80, .4);
            color: #888;
        }}
    """)
    if enabled:
        apply_glow_effect(button, color, 30)
    return button


class HUDPanel(QWidget):
    """Animated HUD panel with enhanced electrified status display."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(24)

        self.status_label = QLabel("⚡ CONTAINMENT STATUS: STANDBY")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 16px;
                font-weight: 700;
                padding: 8px 16px;
                background: rgba(0,255,136,.15);
                border: 2px solid rgba(0,255,136,.5);
                border-radius: 8px;
            }
        """)
        
        self.pulse_label = QLabel("🔋 Bio-Pulse: 0%")
        self.pulse_label.setStyleSheet("""
            QLabel {
                color: #8c5bff;
                font-size: 15px;
                font-weight: 600;
                padding: 6px 14px;
                background: rgba(140,91,255,.15);
                border: 2px solid rgba(140,91,255,.4);
                border-radius: 6px;
            }
        """)
        
        self.latency_label = QLabel("⚡ Latency: 10 ms")
        self.latency_label.setStyleSheet("""
            QLabel {
                color: #00aaff;
                font-size: 15px;
                font-weight: 600;
                padding: 6px 14px;
                background: rgba(0,136,255,.15);
                border: 2px solid rgba(0,136,255,.4);
                border-radius: 6px;
            }
        """)

        layout.addWidget(self.status_label)
        layout.addWidget(self.pulse_label)
        layout.addStretch()
        layout.addWidget(self.latency_label)

        self._hue = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_hud)
        self._timer.start(150)

        apply_glow_effect(self, color="#5dffeb", intensity=20)

    def _update_hud(self) -> None:
        self._hue = (self._hue + 5) % 360
        pulse = 30 + (self._hue % 70)
        latency = 8 + (self._hue % 40)
        
        # Cycle through colors for dynamic effect
        color = QColor.fromHsl(self._hue, 220, 140).name()
        
        self.pulse_label.setText(f"🔋 Bio-Pulse: {pulse}%")
        self.latency_label.setText(f"⚡ Latency: {latency} ms")


class ReaperHeader(QFrame):
    """Top hero bar with live session stats and quick navigation."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(14)

        left = QVBoxLayout()
        self.title = QLabel("THE REAPER IS WATCHING")
        self.title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f4e8ff;")
        self.subtitle = QLabel("Bio-lab containment • Neural feeds • pathogen telemetry")
        self.subtitle.setStyleSheet("font-size: 12px; color: rgba(255,170,205,.75);")
        left.addWidget(self.title)
        left.addWidget(self.subtitle)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(12)
        stats_grid.setVerticalSpacing(4)
        self.session_label = QLabel("Session: —")
        self.time_label = QLabel("Local: --:--:--")
        self.ingress_label = QLabel("Ingress: STANDBY")
        self.target_label = QLabel("Target: —")
        stats_grid.addWidget(self.session_label, 0, 0)
        stats_grid.addWidget(self.time_label, 0, 1)
        stats_grid.addWidget(self.ingress_label, 1, 0)
        stats_grid.addWidget(self.target_label, 1, 1)
        stats_frame = QWidget()
        stats_frame.setLayout(stats_grid)
        left.addWidget(stats_frame)

        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(8)
        left.addLayout(self.buttons)
        layout.addLayout(left, stretch=3)

        glyph_frame = QVBoxLayout()
        glyph_frame.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.glyph = QLabel("☠")
        self.glyph.setStyleSheet("font-size: 42px; color: rgba(198,0,255,.8); padding: 6px 12px;")
        self.glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.glyph.setFixedWidth(64)
        glyph_frame.addWidget(self.glyph)
        layout.addLayout(glyph_frame, stretch=1)

    def add_nav_button(self, text: str, callback, enabled=True) -> None:
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setEnabled(enabled)
        self.buttons.addWidget(btn)

    def update_stats(self, session: str, target: str, ingress: bool, active_jobs: int) -> None:
        self.session_label.setText(f"Session: {session}")
        self.time_label.setText(f"Local: {datetime.now().strftime('%H:%M:%S')}")
        state = "ONLINE" if ingress else "STANDBY"
        self.ingress_label.setText(f"Ingress: {state}")
        self.target_label.setText(f"Target: {target or '—'} | Jobs: {active_jobs}")


class TargetField(QWidget):
    """Reusable target selector with editable combo box."""

    def __init__(self, label: str, parent: Optional[QWidget] = None, *, share_history: bool = True):
        super().__init__(parent)
        self._history: List[str] = []
        self.share_history = share_history

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(QLabel(label))

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        layout.addWidget(self.combo)

        self.scan_btn = QPushButton("Scan Networks")
        self.scan_btn.clicked.connect(self.scan_networks)
        layout.addWidget(self.scan_btn)

    def set_history(self, entries: Iterable[str]) -> None:
        self._history = list(dict.fromkeys(entries))
        current = self.combo.currentText()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self._history)
        self.combo.setCurrentText(current)
        self.combo.blockSignals(False)

    def value(self) -> str:
        return self.combo.currentText().strip()

    def scan_networks(self) -> None:
        """Scan for local network IPs and add to combo."""
        try:
            if IS_WINDOWS:
                # Use ipconfig on Windows
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                ips = []
                for line in result.stdout.splitlines():
                    if "IPv4" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            ip = parts[1].strip()
                            if ip and ip != "127.0.0.1":
                                ips.append(ip)
            else:
                result = subprocess.run(
                    ["ip", "addr", "show"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                ips = []
                for line in result.stdout.splitlines():
                    if "inet " in line and "127.0.0.1" not in line:
                        ip = line.split()[1].split('/')[0]
                        ips.append(ip)
            
            if ips:
                for ip in ips:
                    if ip not in self._history:
                        self._history.append(ip)
                self.set_history(self._history)
                QMessageBox.information(self, "Scan Complete", f"Found IPs: {', '.join(ips)}")
            else:
                QMessageBox.information(self, "Scan Complete", "No local IPs found.")
        except Exception as e:
            QMessageBox.warning(self, "Scan Failed", f"Error scanning networks: {e}")


class CategoryTab(QWidget):
    """Base tab that wraps command execution hooks."""

    def __init__(self, executor, parent=None, wsl_available=False):
        super().__init__(parent)
        self.executor = executor
        self.main_window = parent
        self.wsl_available = wsl_available
        self.panels: List[PanelWindow] = []
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self.workspace = PanelWorkspacePage(columns=2)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.workspace)
        outer.addWidget(self.scroll_area)

    def add_group(self, title: str, description: str) -> QGroupBox:
        group = QGroupBox(title)
        box_layout = QVBoxLayout(group)
        box_layout.setSpacing(8)
        if description:
            info = QLabel(description)
            info.setWordWrap(True)
            box_layout.addWidget(info)
        return group

    def add_panel(self, title: str, widget: QWidget, description: str = "", column_span: int = 1) -> PanelWindow:
        panel = PanelWindow(title, description)
        panel.setContent(widget)
        self.workspace.add_panel(panel, column_span=column_span)
        self.panels.append(panel)
        return panel

    def require_authorization(self, action: str) -> bool:
        """Ask the user to confirm dangerous actions by typing a phrase."""
        phrase = "I AM AUTHORIZED"
        prompt = f"Confirm {action}\nType: {phrase}"
        response, ok = QInputDialog.getText(self, "Confirm action", prompt)
        if not ok:
            return False
        return response.strip().upper() == phrase


class ScanTab(CategoryTab):
    """SCAN tab with Windows-compatible and WSL-based port scanning options."""

    def __init__(self, executor, main_window, wsl_available):
        super().__init__(executor, main_window, wsl_available)
        self.main_window = main_window
        self.target_field = TargetField("Target")
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        self.main_window.register_target_field(self.target_field)

        self.scan_presets = {
            "Quick scan (Test-NetConnection)": self.run_quick,
            "Port scan (1-1000)": self.run_port_scan,
            "Nmap quick (WSL)": self.run_nmap_quick,
            "Nmap full (WSL)": self.run_nmap_full,
        }

        self.add_panel("Target Selection", target_wrap, "Host or network to scan.", column_span=2)
        self.add_panel("Scan Protocols", self.build_scan_group(), column_span=2)

    def build_scan_group(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Scan Protocol"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.scan_presets.keys()))
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(create_glowing_button("Initiate Scan", self.run_selected_preset))
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        grid = QGridLayout()
        grid.setSpacing(12)
        
        grid.addWidget(QLabel("Windows native and Nmap (via WSL) scanning tools"), 0, 0, 1, 2)
        quick_button = create_glowing_button("Quick Test (Test-NetConnection)", self.run_quick)
        grid.addWidget(quick_button, 1, 0)
        port_button = create_glowing_button("Port Scan (PowerShell)", self.run_port_scan)
        grid.addWidget(port_button, 1, 1)
        
        self.nmap_quick_btn = create_glowing_button("Nmap Quick (-T4 -F)", self.run_nmap_quick, enabled=self.wsl_available)
        grid.addWidget(self.nmap_quick_btn, 2, 0)
        
        self.nmap_full_btn = create_glowing_button("Nmap Full (-sS -sV -A)", self.run_nmap_full, enabled=self.wsl_available)
        grid.addWidget(self.nmap_full_btn, 2, 1)

        if not self.wsl_available:
            self.nmap_quick_btn.setToolTip("WSL is not installed. Nmap commands are disabled.")
            self.nmap_full_btn.setToolTip("WSL is not installed. Nmap commands are disabled.")

        layout.addLayout(grid)
        return container

    def run_selected_preset(self) -> None:
        choice = self.preset_combo.currentText()
        runner = self.scan_presets.get(choice)
        if runner:
            runner()

    def validate_target(self) -> Optional[str]:
        value = self.target_field.value()
        if not value:
            QMessageBox.warning(self, "Target missing", "Enter a target before running scans.")
            return None
        return value

    def run_quick(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"Test-NetConnection -ComputerName {quote(target)} -InformationLevel Detailed"
        self.executor(cmd, "Quick scan", target=target)

    def run_port_scan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"1..1000 | ForEach-Object {{ try {{ $socket = New-Object System.Net.Sockets.TcpClient; $socket.Connect({quote(target)}, $_) | Out-Null; Write-Host ('Port {0} is open' -f $_) }} catch {{}} finally {{ if ($socket) {{ $socket.Close() }} }} }}"
        self.executor(cmd, "Port scan (1-1000)", target=target)

    def run_nmap_quick(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap -T4 -F {quote(target)}"
        self.executor(cmd, "Nmap quick scan (WSL)", target=target, is_linux_command=True)

    def run_nmap_full(self) -> None:
        target = self.validate_target()
        if not target:
            return
        if not self.require_authorization("Nmap full scan"):
            self.output_log.appendPlainText("[info] Nmap full scan cancelled (authorization phrase not provided)")
            return
        cmd = f"nmap -sS -sV -A {quote(target)}"
        self.executor(cmd, "Nmap full scan (WSL)", target=target, is_linux_command=True)


class ReconTab(CategoryTab):
    """RECON tab with Windows-compatible and WSL-based discovery tools."""

    def __init__(self, executor, main_window, wsl_available):
        super().__init__(executor, main_window, wsl_available)
        self.target_field = TargetField("Target/Domain")
        main_window.register_target_field(self.target_field)
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        
        self.discovery_options = [
            ("ARP table (arp -a)", "arp -a", "ARP table", False),
            ("DNS lookup (nslookup)", "nslookup {target}", "DNS lookup", False),
            ("Traceroute (tracert)", "tracert {target}", "Trace route", False),
            ("Ping Sweep (WSL nmap)", "nmap -sn {target}", "Ping Sweep (WSL)", True),
        ]
        self.enum_options = [
            ("WHOIS lookup (WSL)", "whois {target}", "WHOIS (WSL)", True),
            ("DNS enum (WSL dnsenum)", "dnsenum {target}", "DNS enum (WSL)", True),
        ]
        self.add_panel("Target Scope", target_wrap, "Provide host, domain, or CIDR", column_span=2)
        self.add_panel("Network Discovery", self.create_discovery_group())
        self.add_panel("Enumeration", self.create_enum_group())

    def create_discovery_group(self) -> QGroupBox:
        group = self.add_group("Network Discovery", "Native and WSL-based discovery tools.")
        btn_layout = QGridLayout()
        btn_layout.setSpacing(6)

        for idx, (label, template, desc, is_wsl) in enumerate(self.discovery_options):
            enabled = not is_wsl or self.wsl_available
            button = create_glowing_button(
                label, lambda template=template, desc=desc, is_wsl=is_wsl: self.run_discovery(template, desc, is_wsl), enabled=enabled
            )
            if not enabled:
                button.setToolTip("WSL is not installed. This command is disabled.")
            btn_layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(btn_layout)
        return group

    def create_enum_group(self) -> QGroupBox:
        group = self.add_group("Enumeration", "DNS, WHOIS, and service enumeration via WSL.")
        layout = QGridLayout()

        for idx, (label, template, desc, is_wsl) in enumerate(self.enum_options):
            enabled = not is_wsl or self.wsl_available
            button = create_glowing_button(
                label, lambda template=template, desc=desc, is_wsl=is_wsl: self.run_enum(template, desc, is_wsl), enabled=enabled
            )
            if not enabled:
                button.setToolTip("WSL is not installed. This command is disabled.")
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        return group

    def run_discovery(self, template: str, description: str, is_wsl: bool) -> None:
        target = self.target_field.value()
        if "{target}" in template and not target:
            QMessageBox.warning(self, "Target missing", "Provide an IP/host/domain.")
            return
        command = template.format(target=quote(target)) if "{target}" in template else template
        self.executor(command, description, target=target or "local", is_linux_command=is_wsl)

    def run_enum(self, template: str, description: str, is_wsl: bool) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a DNS name or host.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target, is_linux_command=is_wsl)


class WebTab(CategoryTab):
    """WEB tab using WSL for advanced scanning."""

    def __init__(self, executor, main_window, wsl_available):
        super().__init__(executor, main_window, wsl_available)
        self.target_field = TargetField("URL / Domain")
        main_window.register_target_field(self.target_field)
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        
        self.web_scanners = [
            ("HTTP Request (Invoke-WebRequest)", "Invoke-WebRequest -Uri {target}", "HTTP request", False),
            ("SSL Test (Test-NetConnection)", "Test-NetConnection -ComputerName {target} -Port 443", "SSL test", False),
            ("Nikto Scan (WSL)", "nikto -host {target}", "Nikto Scan (WSL)", True),
            ("Nuclei Scan (WSL)", "nuclei -u {target}", "Nuclei Scan (WSL)", True),
        ]
        
        self.add_panel("Target URL / Domain", target_wrap, column_span=2)
        self.add_panel("Web Scanners", self.build_web_tools_group())
        if not self.wsl_available:
            info_label = QLabel("Install WSL to enable advanced web scanning tools like Nikto and Nuclei.")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #ffaa00; padding: 10px;")
            info_wrap = QWidget()
            info_layout = QVBoxLayout(info_wrap)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.addWidget(info_label)
            self.add_panel("WSL Notice", info_wrap, column_span=2)

    def build_web_tools_group(self) -> QGroupBox:
        group = self.add_group("Web Scanners", "Native and WSL-based web scanning tools.")
        layout = QGridLayout()

        for idx, (label, template, desc, is_wsl) in enumerate(self.web_scanners):
            enabled = not is_wsl or self.wsl_available
            button = create_glowing_button(
                label, lambda t=template, d=desc, iw=is_wsl: self.run_web_tool(t, d, iw), enabled=enabled
            )
            if not enabled:
                button.setToolTip("WSL is not installed. This command is disabled.")
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        return group

    def run_web_tool(self, template: str, description: str, is_wsl: bool) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a URL before running.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target, is_linux_command=is_wsl)


class WirelessTab(CategoryTab):
    """WIRELESS tab - Provides native Windows commands and a message directing users to use WSL for advanced features."""

    def __init__(self, executor, main_window, wsl_available):
        super().__init__(executor, main_window, wsl_available)
        
        info_label = QLabel(
            "Windows wireless capabilities are limited.\n"
            "Use 'netsh wlan' for basic info. For advanced features like monitor mode, deauth, or WPA cracking, you must use a Linux environment.\n\n"
            "If you have WSL installed, you can use Linux tools through it, but you may need to pass through a USB WiFi adapter to your WSL instance."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #ffaa00; padding: 10px; border: 1px solid #ffaa0033; border-radius: 8px;")
        info_wrap = QWidget()
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.addWidget(info_label)
        
        self.add_panel("Wireless Guidance", info_wrap, column_span=2)
        self.add_panel("Windows WiFi Tools", self.build_windows_wifi_group())

    def build_windows_wifi_group(self) -> QGroupBox:
        group = self.add_group("Windows WiFi Tools", "Basic WiFi operations using netsh.")
        layout = QGridLayout()
        
        show_networks = create_glowing_button("Show Networks", self.show_networks)
        show_profiles = create_glowing_button("Show Profiles", self.show_profiles)
        show_interfaces = create_glowing_button("Show Interfaces", self.show_interfaces)
        
        layout.addWidget(show_networks, 0, 0)
        layout.addWidget(show_profiles, 0, 1)
        layout.addWidget(show_interfaces, 1, 0)
        
        group.layout().addLayout(layout)
        return group

    def show_networks(self) -> None:
        cmd = "netsh wlan show networks"
        self.executor(cmd, "Show WiFi networks", target="local")

    def show_profiles(self) -> None:
        cmd = "netsh wlan show profiles"
        self.executor(cmd, "Show WiFi profiles", target="local")

    def show_interfaces(self) -> None:
        cmd = "netsh wlan show interfaces"
        self.executor(cmd, "Show WiFi interfaces", target="local")


class ToolsTab(CategoryTab):
    """Additional Windows security tools."""

    def __init__(self, executor, main_window, wsl_available):
        super().__init__(executor, main_window, wsl_available)
        self.add_panel("System Tools", self.build_system_tools())
        self.add_panel("Network Tools", self.build_network_tools())

    def build_system_tools(self) -> QGroupBox:
        group = self.add_group("System Tools", "Windows system information and diagnostics.")
        layout = QGridLayout()
        
        sysinfo = create_glowing_button("System Info", lambda: self.executor("systeminfo", "System info"))
        tasklist = create_glowing_button("Task List", lambda: self.executor("tasklist", "Task list"))
        netstat = create_glowing_button("Network Stats", lambda: self.executor("netstat -ano", "Network stats"))
        ipconfig = create_glowing_button("IP Config", lambda: self.executor("ipconfig /all", "IP config"))
        
        layout.addWidget(sysinfo, 0, 0)
        layout.addWidget(tasklist, 0, 1)
        layout.addWidget(netstat, 1, 0)
        layout.addWidget(ipconfig, 1, 1)
        
        group.layout().addLayout(layout)
        return group

    def build_network_tools(self) -> QGroupBox:
        group = self.add_group("Network Tools", "Network diagnostics and testing.")
        layout = QGridLayout()
        
        route = create_glowing_button("Route Table", lambda: self.executor("route print", "Route table"))
        arp = create_glowing_button("ARP Table", lambda: self.executor("arp -a", "ARP table"))
        dns = create_glowing_button("DNS Cache", lambda: self.executor("ipconfig /displaydns", "DNS cache"))
        firewall = create_glowing_button("Firewall Status", lambda: self.executor("netsh advfirewall show allprofiles", "Firewall status"))
        
        layout.addWidget(route, 0, 0)
        layout.addWidget(arp, 0, 1)
        layout.addWidget(dns, 1, 0)
        layout.addWidget(firewall, 1, 1)
        
        group.layout().addLayout(layout)
        return group


class NetReaperGui(QWidget):
    """Main container for the Windows-compatible NetReaper GUI."""

    def __init__(self):
        super().__init__()
        self.wsl_available = is_wsl_available()
        self.setWindowTitle(f"NetReaper GUI - {platform.system()} {'(WSL Available)' if self.wsl_available else '(WSL Not Found)'}")
        self.setMinimumSize(1200, 720)
        self.session_id = uuid4().hex[:8].upper()
        self.ingress_online = False
        self.target_fields: List[TargetField] = []
        self.target_history: List[str] = []
        self.active_threads: List[CommandThread] = []
        self.lite_mode = False
        self.custom_wordlist = ""
        self.wiring_flags = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # Toolbar
        self.toolbar = QToolBar("Actions")
        clear_log_action = QAction("Clear log", self)
        clear_log_action.triggered.connect(self.clear_log)
        self.wiring_flags["clear_log_action"] = True
        self.toolbar.addAction(clear_log_action)
        self.toolbar.addSeparator()
        
        stop_action = QAction("Stop tasks", self)
        stop_action.triggered.connect(self.stop_all_tasks)
        self.toolbar.addAction(stop_action)
        
        lite_action = QAction("Lite mode", self)
        lite_action.setCheckable(True)
        lite_action.setChecked(False)
        lite_action.triggered.connect(self.toggle_lite_mode)
        self.toolbar.addAction(lite_action)
        
        config_action = QAction("Edit config", self)
        config_action.triggered.connect(self.edit_config)
        self.toolbar.addAction(config_action)
        
        main_layout.addWidget(self.toolbar)

        # Header and HUD
        self.reaper_header = ReaperHeader()
        main_layout.addWidget(self.reaper_header)

        self.hud_panel = HUDPanel()
        main_layout.addWidget(self.hud_panel)

        central_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_splitter.setChildrenCollapsible(False)

        nav_container = QFrame()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(8)
        nav_label = QLabel("Navigation")
        nav_label.setStyleSheet("font-weight: 700;")
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setAlternatingRowColors(True)
        nav_layout.addWidget(nav_label)
        nav_layout.addWidget(self.nav_list, 1)
        central_splitter.addWidget(nav_container)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setChildrenCollapsible(False)
        self.workspace_stack = QStackedWidget()
        right_splitter.addWidget(self.workspace_stack)
        self.operations_deck = self.build_operations_deck()
        right_splitter.addWidget(self.operations_deck)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)
        central_splitter.addWidget(right_splitter)
        central_splitter.setStretchFactor(0, 0)
        central_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(central_splitter, stretch=1)

        # Create pages
        self.scan_tab = ScanTab(self.execute_command, self, self.wsl_available)
        self.recon_tab = ReconTab(self.execute_command, self, self.wsl_available)
        self.web_tab = WebTab(self.execute_command, self, self.wsl_available)
        self.wireless_tab = WirelessTab(self.execute_command, self, self.wsl_available)
        self.tools_tab = ToolsTab(self.execute_command, self, self.wsl_available)
        
        self.pages = [
            ("Scan", self.scan_tab),
            ("Recon", self.recon_tab),
            ("Web", self.web_tab),
            ("Wireless", self.wireless_tab),
            ("Tools", self.tools_tab),
        ]
        self.page_lookup = {}
        for idx, (name, widget) in enumerate(self.pages):
            self.workspace_stack.addWidget(widget)
            self.page_lookup[name] = idx
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self.workspace_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        self.reaper_header.add_nav_button("Scan", lambda: self.navigate_to("Scan"))
        self.reaper_header.add_nav_button("Recon", lambda: self.navigate_to("Recon"))
        self.reaper_header.add_nav_button("Web", lambda: self.navigate_to("Web"), enabled=self.wsl_available)
        self.reaper_header.add_nav_button("Wireless", lambda: self.navigate_to("Wireless"))
        self.reaper_header.add_nav_button("Tools", lambda: self.navigate_to("Tools"))

        # Load history
        self._load_target_history()
        for field in self.target_fields:
            field.set_history(self.target_history)

        # Timer for header updates
        self.hero_timer = QTimer(self)
        self.hero_timer.timeout.connect(self.refresh_reaper_header)
        self.hero_timer.start(1000)
        self.refresh_reaper_header()

        # Show platform info
        self.output_log.appendPlainText(f"NetReaper GUI initialized on {platform.system()} {platform.release()}")
        if self.wsl_available:
            self.output_log.appendPlainText("[info] WSL detected. Linux tools are available.")
        else:
            self.output_log.appendPlainText("[warning] WSL not found. Linux-specific tools are disabled.")
        self.output_log.appendPlainText(f"Session ID: {self.session_id}\n")
        self.run_ui_debug_checks()

    def build_operations_deck(self) -> QWidget:
        deck = QSplitter(Qt.Orientation.Horizontal)
        deck.setChildrenCollapsible(False)

        self.output_panel = PanelWindow("Operations Console", "Live command output and controls")
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(6, 6, 6, 6)
        output_layout.setSpacing(8)

        status_row = QHBoxLayout()
        self.output_status_label = QLabel("Status: idle")
        self.output_status_label.setStyleSheet("font-weight: 700;")
        self.current_command_label = QLabel("Command: none")
        self.current_command_label.setWordWrap(True)
        status_row.addWidget(self.output_status_label)
        status_row.addWidget(self.current_command_label, 1)

        action_row = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self.copy_log)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        save_btn = QPushButton("Save Log")
        save_btn.clicked.connect(self.save_log)
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.filter_log)
        for btn in (copy_btn, clear_btn, save_btn, filter_btn):
            action_row.addWidget(btn)
        action_row.addStretch()

        self.output_log = QPlainTextEdit()
        self.output_log.setObjectName("outputLog")
        self.output_log.setReadOnly(True)
        self.output_log.setMinimumHeight(200)

        input_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("commandInput")
        self.cmd_input.setPlaceholderText("Enter command (prefix with 'wsl' for Linux commands)")
        self.cmd_input.returnPressed.connect(self.execute_cmd_input)
        self.wiring_flags["cmd_input"] = True
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.execute_cmd_input)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_all_tasks)
        input_row.addWidget(self.cmd_input, 1)
        input_row.addWidget(run_btn)
        input_row.addWidget(stop_btn)

        output_layout.addLayout(status_row)
        output_layout.addLayout(action_row)
        output_layout.addWidget(self.output_log, 1)
        output_layout.addLayout(input_row)
        self.output_panel.setContent(output_container)
        deck.addWidget(self.output_panel)

        self.history_panel = PanelWindow("History", "Double-click to replay commands")
        history_container = QWidget()
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(6, 6, 6, 6)
        history_layout.setSpacing(6)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.replay_command)
        self.wiring_flags["history_double_click"] = True
        history_layout.addWidget(self.history_list)
        self.history_panel.setContent(history_container)
        deck.addWidget(self.history_panel)
        deck.setStretchFactor(0, 3)
        deck.setStretchFactor(1, 1)
        self.output_panel.set_status("#3dd598")
        self.history_panel.set_status("#3dd598")
        return deck

    def _wrap_in_workspace(self, title: str, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        workspace = PanelWorkspacePage(columns=1)
        panel = PanelWindow(title)
        panel.setContent(widget)
        workspace.add_panel(panel, column_span=1)
        layout.addWidget(workspace)
        return page

    def navigate_to(self, name: str) -> None:
        idx = self.page_lookup.get(name)
        if idx is None:
            return
        self.nav_list.setCurrentRow(idx)
        self.workspace_stack.setCurrentIndex(idx)

    def run_ui_debug_checks(self) -> None:
        if os.environ.get("NETREAPER_GUI_DEBUG") != "1":
            return
        checks = [
            ("output_log", hasattr(self, "output_log")),
            ("cmd_input", hasattr(self, "cmd_input")),
            ("history_list", hasattr(self, "history_list")),
            ("nav_list", hasattr(self, "nav_list")),
            ("pages", bool(getattr(self, "pages", []))),
        ]
        signal_checks = [
            ("cmd_input.returnPressed", self.wiring_flags.get("cmd_input", False)),
            ("history_list.doubleClick", self.wiring_flags.get("history_double_click", False)),
            ("clear_log_action", self.wiring_flags.get("clear_log_action", False)),
        ]
        report: List[str] = []
        for name, ok in checks + signal_checks:
            line = f"[{'OK' if ok else 'MISS'}] {name}"
            report.append(line)
            if not ok:
                raise AssertionError(f"UI wiring missing: {name}")
        summary = "UI wiring OK"
        print(summary)
        for line in report:
            print(line)
        self.output_log.appendPlainText(summary)
        for line in report:
            self.output_log.appendPlainText(line)
    def register_target_field(self, field: TargetField) -> None:
        if not field.share_history:
            return
        if field not in self.target_fields:
            self.target_fields.append(field)
            if self.target_history:
                field.set_history(self.target_history)

    def add_target_history(self, target: str) -> None:
        if not target:
            return
        history = [target] + [t for t in self.target_history if t != target]
        self.target_history = history[:20]
        for field in self.target_fields:
            field.set_history(history)

    def _load_target_history(self) -> None:
        """Load target history from config directory."""
        config_dir = get_config_dir()
        history_file = os.path.join(config_dir, "history", "targets.log")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    loaded = []
                    for line in f:
                        target = line.strip().split()[0] if line.strip() else ""
                        if target and target not in loaded:
                            loaded.append(target)
                    self.target_history = loaded[:20]
            except OSError:
                pass


    def execute_command(self, command: str, description: str, target: Optional[str] = None, is_linux_command: bool = False) -> None:
        """Execute a shell command with Windows/WSL compatibility and security hardening."""
        
        if is_linux_command:
            if not self.wsl_available:
                QMessageBox.warning(self, "WSL Required", f"The command '{command.split()[0]}' requires WSL, which was not found.")
                return
            wrapped_cmd = command
            if self.lite_mode:
                wrapped_cmd = f"NR_LITE_MODE=1 {wrapped_cmd}"
            argv = ["wsl.exe", "bash", "-lc", wrapped_cmd]
            log_command = sanitize_command_for_display(wrapped_cmd)
        else:
            cmd_to_run = command
            if self.lite_mode:
                cmd_to_run = f"$env:NR_LITE_MODE=1; {cmd_to_run}"
            argv = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd_to_run]
            log_command = sanitize_command_for_display(cmd_to_run)

        self.current_command_label.setText(f"Command: {log_command}")
        self.output_status_label.setText(f"Status: running ({description})")
        self.output_panel.set_status("#5ad6ff")
        self.history_panel.set_status("#5ad6ff")
        self.output_log.appendPlainText(f"[{description}] $ {log_command}")
        
        if target:
            self.add_target_history(target)
        
        thread = CommandThread(argv, sanitize_output=True)
        thread.output.connect(self.output_log.appendPlainText)
        thread.finished.connect(self.on_finished)
        thread.finished.connect(lambda _: self.resize_log())
        self.active_threads.append(thread)
        thread.finished.connect(lambda code, thr=thread: self.cleanup_thread(thr))
        self.ingress_online = True
        self.refresh_reaper_header()
        thread.start()
        
        item = QListWidgetItem(f"{description}: {log_command}")
        item.setData(Qt.ItemDataRole.UserRole, command)  # Store the original command for replay
        self.history_list.addItem(item)
    
    def _sanitize_command_for_log(self, command: str) -> str:
        """Redact sensitive information from commands before logging."""
        import re
        command = re.sub(r'(-p|--password|--passwd)\s+\S+', r'\1 ***REDACTED***', command, flags=re.IGNORECASE)
        command = re.sub(r'(api[_-]?key|token)[=:]\S+', r'\1=***REDACTED***', command, flags=re.IGNORECASE)
        command = re.sub(r'(Authorization|Bearer)[:\s]+\S+', r'\1: ***REDACTED***', command, flags=re.IGNORECASE)
        return command

    def cleanup_thread(self, thread: CommandThread) -> None:
        if thread in self.active_threads:
            self.active_threads.remove(thread)
        if not self.active_threads:
            self.ingress_online = False
        self.refresh_reaper_header()

    def on_finished(self, return_code: int) -> None:
        self.output_log.appendPlainText(f"[status] Return code: {return_code}\n")
        status_text = f"Status: finished (code {return_code})"
        self.output_status_label.setText(status_text)
        color = "#3dd598" if return_code == 0 else "#ff7b7b"
        self.output_panel.set_status(color)
        self.history_panel.set_status(color)

    def clear_log(self) -> None:
        self.output_log.clear()
        self.output_status_label.setText("Status: idle")
        self.current_command_label.setText("Command: none")
        self.output_panel.set_status("#3dd598")
        self.history_panel.set_status("#3dd598")

    def copy_log(self) -> None:
        self.output_log.selectAll()
        self.output_log.copy()
        cursor = self.output_log.textCursor()
        cursor.clearSelection()
        self.output_log.setTextCursor(cursor)

    def save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save NetReaper log",
            os.path.expanduser("~/netreaper.log"),
            "Text files (*.txt);;All files (*.*)",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(self.output_log.toPlainText())
                self.output_log.appendPlainText(f"[info] Saved log to {path}")
            except OSError as exc:
                QMessageBox.warning(self, "Save failed", str(exc))

    def filter_log(self) -> None:
        term, ok = QInputDialog.getText(self, "Filter output", "Show lines containing:")
        if not ok or not term:
            return
        lines = [
            line for line in self.output_log.toPlainText().splitlines()
            if term.lower() in line.lower()
        ]
        preview = "\n".join(lines[:60]) or "No matches."
        QMessageBox.information(self, "Filter results", preview)

    def resize_log(self) -> None:
        cursor = self.output_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_log.setTextCursor(cursor)

    def replay_command(self, item: QListWidgetItem) -> None:
        command = item.data(Qt.ItemDataRole.UserRole)
        # Description is part of the item text
        description = item.text().split(":")[0]
        if command:
            # Re-check if it's a linux command to apply WSL logic
            # A bit of a simplification, but effective for the button-based commands.
            is_linux = any(tool in command for tool in ["nmap", "whois", "dnsenum", "nikto", "nuclei"])
            self.execute_command(command, f"Re-run: {description}", is_linux_command=is_linux)

    def refresh_reaper_header(self) -> None:
        target = ""
        if self.target_fields:
            target = self.target_fields[0].value()
        self.reaper_header.update_stats(
            self.session_id,
            target,
            self.ingress_online,
            len(self.active_threads),
        )

    def switch_to_tab(self, widget: QWidget) -> None:
        for idx, (_, page_widget) in enumerate(self.pages):
            if page_widget is widget:
                self.nav_list.setCurrentRow(idx)
                self.workspace_stack.setCurrentIndex(idx)
                return

    def execute_cmd_input(self) -> None:
        cmd = self.cmd_input.text().strip()
        if cmd:
            is_linux = cmd.startswith("wsl ")
            actual_cmd = cmd[4:] if is_linux else cmd
            self.output_log.appendPlainText(f"> {cmd}")
            self.execute_command(actual_cmd, "Manual Command", is_linux_command=is_linux)
            self.cmd_input.clear()

    def stop_all_tasks(self) -> None:
        """Terminate all running command threads."""
        if not self.active_threads:
            self.output_log.appendPlainText("[info] No active tasks to stop")
            return
        self.output_log.appendPlainText("[info] Stopping all active tasks...")
        for thread in list(self.active_threads):
            try:
                thread.terminate()
            except Exception as e:
                self.output_log.appendPlainText(f"[error] Could not stop thread: {e}")
        self.active_threads.clear()
        self.ingress_online = False
        self.refresh_reaper_header()
        self.output_status_label.setText("Status: stopped")
        self.output_panel.set_status("#ff7b7b")
        self.history_panel.set_status("#ff7b7b")

    def toggle_lite_mode(self, enabled: bool) -> None:
        """Toggle Lite mode on or off."""
        self.lite_mode = bool(enabled)
        mode = "enabled" if self.lite_mode else "disabled"
        if hasattr(self, "hud_panel") and self.hud_panel:
            if self.lite_mode:
                self.hud_panel.status_label.setText("CONTAINMENT STATUS: LITE MODE")
            else:
                self.hud_panel.status_label.setText("CONTAINMENT STATUS: STANDBY")
        self.output_log.appendPlainText(f"[info] Lite mode {mode}")
        self.output_status_label.setText(f"Status: lite mode {mode}")
        self.output_panel.set_status("#5ad6ff" if self.lite_mode else "#3dd598")

    def edit_config(self) -> None:
        """Open a simple editor for the configuration file."""
        from PyQt6.QtWidgets import QDialog
        
        config_dir = get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.conf")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "# NetReaper user configuration\n"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit NetReaper Config")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        edit = QPlainTextEdit()
        edit.setPlainText(content)
        layout.addWidget(edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        def save_config() -> None:
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(edit.toPlainText())
                QMessageBox.information(self, "Saved", f"Config saved to {config_path}")
                dialog.accept()
            except Exception as exc:
                QMessageBox.warning(self, "Error", f"Failed to save config: {exc}")
        
        save_btn.clicked.connect(save_config)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.resize(600, 500)
        dialog.exec()


def main() -> None:
    """Main entry point for the NetReaper GUI."""
    app = QApplication(sys.argv)
    apply_bio_theme(app)

    window = QWidget()
    layout = QVBoxLayout(window)
    gui = NetReaperGui()
    layout.addWidget(gui)

    window.setWindowTitle(f"NetReaper Command Center - {platform.system()}")
    window.resize(1280, 900)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
