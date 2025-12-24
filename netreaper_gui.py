#!/usr/bin/env python3
"""
NetReaper GUI — Cyberpunk dark native toolkit interface.

Reimplements the CLI SCAN, RECON, WIRELESS, and WEB flows using PyQt6 so the
toolset is fully usable from a windowed interface without losing the Brass
hammer controls that security engineers expect.
"""

from __future__ import annotations

import shlex
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Iterable, List, Optional, Tuple
from uuid import uuid4

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, QThread, pyqtSignal, QObject, QUrl

import shutil  # For checking tool availability

import os  # Added for interface discovery and history loading
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
    QProgressBar,
)

# Optional WebEngine for embedded HTML (holographic map)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BASE_DIR.parent))

from gui_components import PanelWindow, PanelWorkspacePage
from gui_theme import apply_bio_theme
from security_utils import sanitize_command_for_display




class CommandThread(QThread):
    """Runs a shell command and emits its output line by line.

    SECURITY: Uses argv lists with shell=False to prevent command injection.
    Handles sudo by piping the password to stdin, avoiding password exposure.
    """

    output = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command: Iterable[str] | str, sudo_password: Optional[str] = None, sanitize_output: bool = True):
        super().__init__()
        self.command = command
        self.sudo_password = sudo_password
        self.sanitize_output = sanitize_output
        self.process: Optional[subprocess.Popen] = None

    def _build_argv(self) -> List[str]:
        if isinstance(self.command, (list, tuple)):
            return list(self.command)
        return shlex.split(self.command)

    def run(self) -> None:
        try:
            cmd_args = self._build_argv()

            # SECURITY & RELIABILITY: Use a new process group to manage child processes.
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                preexec_fn = None
            else:
                creationflags = 0
                preexec_fn = os.setsid

            if cmd_args and cmd_args[0] == "sudo":
                cmd_args.insert(1, "-S")
                self.process = subprocess.Popen(
                    cmd_args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=preexec_fn,
                    creationflags=creationflags,
                )
                if self.process.stdin:
                    if self.sudo_password:
                        self.process.stdin.write(self.sudo_password + "\n")
                        self.process.stdin.flush()
                    self.process.stdin.close()
            else:
                self.process = subprocess.Popen(
                    cmd_args,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=preexec_fn,
                    creationflags=creationflags,
                )
        except (FileNotFoundError, OSError, ValueError) as exc:
            self.output.emit(f"[error] {exc}")
            self.finished.emit(1)
            return

        assert self.process.stdout
        for line in iter(self.process.stdout.readline, ""):
            output_line = line.rstrip()
            if "sudo: a password is required" in output_line.lower() or "sudo: incorrect password" in output_line.lower():
                self.output.emit("[error] Sudo password was incorrect or is required.")
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
        """Terminate the underlying process group if it is running."""
        if not self.process or self.process.poll() is not None:
            return
        try:
            if sys.platform == "win32":
                try:
                    self.process.send_signal(subprocess.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                    time.sleep(0.3)
                except Exception:
                    pass
                if self.process.poll() is None:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
                self.output.emit("[status] Task terminated.")
                return

            # POSIX path
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, 15)  # SIGTERM
            time.sleep(0.5)
            if self.process.poll() is None:
                os.killpg(pgid, 9)  # SIGKILL
            self.output.emit("[status] Task terminated.")
        except (ProcessLookupError, PermissionError):
            try:
                self.process.terminate()
            except Exception:
                pass
        except Exception:
            try:
                self.process.terminate()
            except Exception:
                pass


def quote(value: Optional[str]) -> str:
    if value is None:
        return ""
    return shlex.quote(value.strip())


def apply_glow_effect(widget: QWidget, color: str = "#7c5dff") -> None:
    """Add a pulsating glow effect via drop shadow animation."""

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(14)
    effect.setColor(QColor(color))
    effect.setOffset(0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"blurRadius", widget)
    animation.setStartValue(10)
    animation.setEndValue(32)
    animation.setDuration(2100)
    animation.setLoopCount(-1)
    try:
        animation.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutQuad))
    except Exception:
        try:
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        except Exception:
            pass
    animation.start()
    widget._glow_animation = animation


def create_glowing_button(text: str, callback) -> QPushButton:
    button = QPushButton(text)
    button.clicked.connect(lambda checked=False, cb=callback: cb())
    apply_glow_effect(button, color="#c87bff")
    return button


class HUDPanel(QWidget):
    """Animated HUD panel that shows status pulses and accent colors."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("hudPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(16)

        self.status_label = QLabel("CONTAINMENT STATUS: STANDBY")
        self.status_label.setObjectName("hudLabel")
        self.pulse_label = QLabel("Bio-Pulse: 0%")
        self.pulse_label.setObjectName("hudLabel")
        self.latency_label = QLabel("Latency: 10 ms")
        self.latency_label.setObjectName("hudLabel")

        layout.addWidget(self.status_label)
        layout.addWidget(self.pulse_label)
        layout.addStretch()
        layout.addWidget(self.latency_label)

        self._hue = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_hud)
        self._timer.start(220)

        apply_glow_effect(self, color="#5dffeb")

    def _update_hud(self) -> None:
        self._hue = (self._hue + 8) % 360
        pulse = 30 + (self._hue % 70)
        latency = 8 + (self._hue % 40)
        color = QColor.fromHsl(self._hue, 220, 120).name()
        for label in (self.status_label, self.pulse_label, self.latency_label):
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.pulse_label.setText(f"Bio-Pulse: {pulse}%")
        self.latency_label.setText(f"Latency: {latency} ms")


class ReaperHeader(QFrame):
    """Top hero bar with live session stats and quick navigation."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("reaperHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(14)

        left = QVBoxLayout()
        self.title = QLabel("THE REAPER IS WATCHING")
        self.title.setObjectName("reaperTitle")
        self.subtitle = QLabel("Bio-lab containment • Neural feeds • pathogen telemetry")
        self.subtitle.setObjectName("reaperSubtitle")
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
        stats_frame.setObjectName("reaperStats")
        stats_frame.setLayout(stats_grid)
        left.addWidget(stats_frame)

        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(8)
        left.addLayout(self.buttons)
        layout.addLayout(left, stretch=3)

        glyph_frame = QVBoxLayout()
        glyph_frame.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.glyph = QLabel("☠")
        self.glyph.setObjectName("reaperGlyph")
        self.glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.glyph.setFixedWidth(64)
        glyph_frame.addWidget(self.glyph)
        layout.addLayout(glyph_frame, stretch=1)

    def add_nav_button(self, text: str, callback) -> None:
        btn = QPushButton(text)
        btn.clicked.connect(callback)
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
            result = subprocess.run(
                ["ip", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ips = []
            for line in result.stdout.splitlines():
                if "inet " in line and not "127.0.0.1" in line:
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

    def __init__(self, executor, parent=None):
        super().__init__(parent)
        self.executor = executor
        self.main_window = parent
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


# ════════════════════════════════════════════════════════════════════════════
# Wizard and Job Tabs
# ════════════════════════════════════════════════════════════════════════════

class JobsTab(QWidget):
    """Simple job status page that displays the current job queue."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        self.refresh_button = QPushButton("Refresh Jobs")
        self.refresh_button.clicked.connect(self.refresh_jobs)
        layout.addWidget(self.refresh_button)
        self.job_display = QPlainTextEdit()
        self.job_display.setReadOnly(True)
        self.job_display.setPlaceholderText("Job queue will appear here...")
        layout.addWidget(self.job_display)
        self.refresh_jobs()

    def refresh_jobs(self) -> None:
        import json  # Imported lazily to avoid overhead on startup
        job_file = os.path.expanduser("~/.netreaper/jobs.json")
        if not os.path.exists(job_file):
            self.job_display.setPlainText("No jobs defined.")
            return
        try:
            with open(job_file, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        except Exception as exc:
            self.job_display.setPlainText(f"Error loading jobs: {exc}")
            return
        if not jobs:
            self.job_display.setPlainText("No jobs in queue.")
            return
        lines: List[str] = []
        header = f"{'ID':8} | {'Status':8} | {'Wizard':12} | {'Target':15} | {'Created'}"
        lines.append(header)
        lines.append("-" * len(header))
        for job_id, job in jobs.items():
            status = job.get("status", "unknown")
            wizard = job.get("wizard", "")
            target = job.get("target", "")
            created = job.get("created_at", "")
            lines.append(f"{job_id[:8]:8} | {status:8} | {wizard:12} | {target:15} | {created}")
        self.job_display.setPlainText("\n".join(lines))



class DiscoveryThread(QThread):
    """Background discovery for interfaces, nearby Wi‑Fi APs, and neighbor hosts."""

    log = pyqtSignal(str)
    result = pyqtSignal(dict)

    def __init__(self, *, rescan_wifi: bool = True, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.rescan_wifi = rescan_wifi

    def run(self) -> None:
        payload = {"interfaces": [], "aps": [], "hosts": [], "errors": []}

        def has(cmd: str) -> bool:
            return shutil.which(cmd) is not None

        # Interfaces
        try:
            if has("ip"):
                p = subprocess.run(["ip", "-j", "addr", "show"], capture_output=True, text=True)
                if p.returncode == 0:
                    data = json.loads(p.stdout or "[]")
                    for it in data:
                        name = it.get("ifname") or ""
                        state = it.get("operstate") or ""
                        mac = it.get("address") or ""
                        ipv4, ipv6 = [], []
                        for ai in it.get("addr_info", []) or []:
                            fam = ai.get("family")
                            local = ai.get("local")
                            if not local:
                                continue
                            if fam == "inet":
                                ipv4.append(local)
                            elif fam == "inet6":
                                ipv6.append(local)
                        payload["interfaces"].append({"name": name, "state": state, "mac": mac, "ipv4": ipv4, "ipv6": ipv6})
                else:
                    payload["errors"].append("Interface discovery failed (ip).")
                    self.log.emit(f"[DISCOVERY] ip error: {p.stderr.strip()}")
            else:
                payload["errors"].append("Missing tool: ip (interface discovery unavailable).")
        except Exception as e:
            payload["errors"].append("Interface discovery error.")
            self.log.emit(f"[DISCOVERY] Interface exception: {e!r}")

        # Neighbors / ARP
        try:
            if has("ip"):
                p = subprocess.run(["ip", "neigh"], capture_output=True, text=True)
                if p.returncode == 0:
                    for line in (p.stdout or "").splitlines():
                        parts = line.split()
                        if not parts:
                            continue
                        ip_addr = parts[0]
                        mac = ""
                        state = parts[-1] if parts else ""
                        if "lladdr" in parts:
                            try:
                                mac = parts[parts.index("lladdr") + 1]
                            except Exception:
                                mac = ""
                        payload["hosts"].append({"ip": ip_addr, "mac": mac, "state": state})
                else:
                    payload["errors"].append("Neighbor discovery failed (ip neigh).")
                    self.log.emit(f"[DISCOVERY] ip neigh error: {p.stderr.strip()}")
            else:
                payload["errors"].append("Missing tool: ip (neighbor discovery unavailable).")
        except Exception as e:
            payload["errors"].append("Neighbor discovery error.")
            self.log.emit(f"[DISCOVERY] Neighbor exception: {e!r}")

        # Wi‑Fi scan
        try:
            if has("nmcli"):
                cmd = ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"]
                if self.rescan_wifi:
                    cmd += ["--rescan", "yes"]
                p = subprocess.run(cmd, capture_output=True, text=True)
                if p.returncode == 0:
                    for raw in (p.stdout or "").splitlines():
                        if not raw.strip():
                            continue
                        parts = raw.rsplit(":", 4)
                        if len(parts) != 5:
                            continue
                        ssid, bssid, chan, signal, security = parts
                        ssid = ssid.strip()
                        bssid = bssid.strip()
                        try:
                            chan_i = int(chan.strip()) if chan.strip() else None
                        except Exception:
                            chan_i = None
                        try:
                            sig_i = int(signal.strip()) if signal.strip() else 0
                        except Exception:
                            sig_i = 0
                        payload["aps"].append({"ssid": ssid, "bssid": bssid, "chan": chan_i, "signal": sig_i, "security": security.strip()})
                else:
                    payload["errors"].append("Wi‑Fi scan failed (nmcli).")
                    self.log.emit(f"[DISCOVERY] nmcli error: {p.stderr.strip()}")
            else:
                payload["errors"].append("Missing tool: nmcli (Wi‑Fi discovery unavailable).")
        except Exception as e:
            payload["errors"].append("Wi‑Fi discovery error.")
            self.log.emit(f"[DISCOVERY] Wi‑Fi exception: {e!r}")

        self.result.emit(payload)


class WizardTab(QWidget):
    """Flagship REAPER MODE tab with extensive automation, guided workflows, and rock-solid error handling."""

    def __init__(self, executor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.executor = executor
        self.main_window = parent
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(16)

        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Web Recon Wizard", "Credential Hunting Wizard", "Wireless Takeover Wizard", "Full Recon Wizard"])
        self.mode_combo.currentTextChanged.connect(self.update_mode_ui)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Select Reaper Mode:"))
        mode_layout.addWidget(self.mode_combo)
        self.layout.addLayout(mode_layout)

        # Target input
        self.target_field = TargetField("Target")
        self.target_field.combo.setPlaceholderText("Enter target (IP, domain, subnet, or interface)")
        self.layout.addWidget(self.target_field)
        if self.main_window:
            self.main_window.register_target_field(self.target_field)

        # Options group
        self.options_group = QGroupBox("Automation Options")
        options_layout = QVBoxLayout(self.options_group)
        self.aggressive_check = QCheckBox("Aggressive mode (faster but more detectable)")
        self.aggressive_check.setChecked(False)
        options_layout.addWidget(self.aggressive_check)
        self.verbose_check = QCheckBox("Verbose output")
        self.verbose_check.setChecked(True)
        options_layout.addWidget(self.verbose_check)
        self.save_results_check = QCheckBox("Save results to file")
        self.save_results_check.setChecked(True)
        options_layout.addWidget(self.save_results_check)
        self.layout.addWidget(self.options_group)

        # Progress and status
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.status_label = QLabel("Ready to deploy Reaper Mode.")
        self.status_label.setStyleSheet("color: #f4e8ff; font-weight: bold;")
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress)

        # Launch button
        self.launch_button = create_glowing_button("Deploy Reaper Mode", self.launch_reaper)
        self.layout.addWidget(self.launch_button)

        # Initialize UI
        self.update_mode_ui()

    def update_mode_ui(self):
        mode = self.mode_combo.currentText()
        if mode == "Web Recon Wizard":
            self.target_field.combo.setPlaceholderText("Target domain or IP")
            self.aggressive_check.setText("Aggressive scanning (full enumeration)")
        elif mode == "Credential Hunting Wizard":
            self.target_field.combo.setPlaceholderText("Target IP or domain")
            self.aggressive_check.setText("Brute force enabled")
        elif mode == "Wireless Takeover Wizard":
            self.target_field.combo.setPlaceholderText("Wireless interface (optional)")
            self.aggressive_check.setText("Auto-crack handshakes")
        elif mode == "Full Recon Wizard":
            self.target_field.combo.setPlaceholderText("Target IP, domain, or subnet")
            self.aggressive_check.setText("Comprehensive sweep")

    def launch_reaper(self):
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target Required", "Please enter a valid target for Reaper Mode.")
            return

        mode = self.mode_combo.currentText()
        aggressive = self.aggressive_check.isChecked()
        verbose = self.verbose_check.isChecked()
        save_results = self.save_results_check.isChecked()

        # Build command with options
        base_cmd = f"netreaper wizard {self.get_wizard_type(mode)} {shlex.quote(target)}"
        if aggressive:
            base_cmd += " --aggressive"
        if verbose:
            base_cmd += " --verbose"
        if save_results:
            base_cmd += f" --output /tmp/reaper_{mode.lower().replace(' ', '_')}_{int(time.time())}.log"

        self.status_label.setText(f"Deploying {mode}...")
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.launch_button.setEnabled(False)

        try:
            self._start_command(base_cmd, mode)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.progress.setVisible(False)
            self.launch_button.setEnabled(True)

    def get_wizard_type(self, mode):
        if mode == "Web Recon Wizard":
            return "web"
        elif mode == "Credential Hunting Wizard":
            return "creds"
        elif mode == "Wireless Takeover Wizard":
            return "wifi"
        elif mode == "Full Recon Wizard":
            return "recon"
        return "web"

    def _start_command(self, command: str, description: str) -> None:
        """Launch a wizard with enhanced error handling and progress tracking."""
        self.progress.setValue(10)
        
        # Check for sudo and prompt if needed
        if command.strip().startswith("sudo"):
            password, ok = QInputDialog.getText(self.main_window, "Sudo Password", "Enter your password for sudo:", QLineEdit.EchoMode.Password)
            if not ok:
                self.status_label.setText("Sudo required, but password not provided.")
                self.progress.setVisible(False)
                self.launch_button.setEnabled(True)
                return
            thread = CommandThread(command, sudo_password=password)
        else:
            thread = CommandThread(command)

        def handle_output(line: str) -> None:
            mw: NetReaperGui = self.parent()
            if hasattr(mw, "output_log"):
                mw.output_log.appendPlainText(line)
            if "Progress:" in line:
                import re
                m = re.search(r"\[(\d+)/(\d+)\]", line)
                if m:
                    try:
                        cur = int(m.group(1))
                        total = int(m.group(2))
                        val = int(100 * cur / total)
                        self.progress.setValue(max(10, min(90, val)))
                    except Exception:
                        pass
        thread.output.connect(handle_output)
        def on_finished(code: int) -> None:
            self.progress.setValue(100)
            if code == 0:
                self.status_label.setText(f"{description} completed successfully.")
            else:
                self.status_label.setText(f"{description} failed with code {code}.")
            QTimer.singleShot(3000, lambda: self.progress.setVisible(False))
            self.launch_button.setEnabled(True)
        thread.finished.connect(on_finished)
        thread.start()

    def run_web(self) -> None:
        target = self.web_target.text().strip()
        if not target:
            QMessageBox.warning(self, "Missing target", "Please enter a target domain or IP")
            return
        cmd = f"netreaper wizard web {shlex.quote(target)}"
        self._start_command(cmd, "Web wizard")

    def run_creds(self) -> None:
        target = self.creds_target.text().strip()
        if not target:
            QMessageBox.warning(self, "Missing target", "Please enter a target IP or domain")
            return
        cmd = f"netreaper wizard creds {shlex.quote(target)}"
        self._start_command(cmd, "Creds wizard")

    def run_wifi(self) -> None:
        iface = self.wifi_iface.text().strip()
        # iface is optional; if blank, netreaper will auto‑select
        cmd = "netreaper wizard wifi"
        if iface:
            cmd += f" {shlex.quote(iface)}"
        self._start_command(cmd, "WiFi wizard")


class ScanTab(CategoryTab):
    """SCAN tab with all port scanning options."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.main_window = main_window
        self.target_field = TargetField("Target")
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        self.discovery_panel = self._build_discovery_panel()
        target_layout.addWidget(self.discovery_panel)

        # Ensure the Scan Networks button triggers structured discovery
        try:
            self.target_field.scan_btn.clicked.disconnect()
        except Exception:
            pass
        self.target_field.scan_btn.clicked.connect(self.main_window.start_discovery)
        self.main_window.register_target_field(self.target_field)

        self.scan_presets = {
            "Quick scan (-T4 -F)": self.run_quick,
            "Full scan (-sS -sV -sC -A -p-)": self.run_full,
            "Stealth scan (-sS -T2 -f)": self.run_stealth,
            "UDP scan (-sU --top-ports)": self.run_udp,
            "Vuln scan (--script vuln)": self.run_vuln,
        }

        self.add_panel("Target Selection", target_wrap, "Set the host/network to scan.", column_span=2)
        self.add_panel("Preset Profiles", self.build_genome_group())
        self.add_panel("Sequencing Routines", self.build_sequencing_group(), column_span=2)
        self.add_panel("Specialized Scans", self.build_mass_group())


    def _build_discovery_panel(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("discoveryPanel")
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)

        self.holo_view = None
        if QWebEngineView is not None:
            self.holo_view = QWebEngineView()
            self.holo_view.setObjectName("holoMapView")
            self.holo_view.setMinimumHeight(320)
            self.holo_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "holo_map", "index.html"))
            self.holo_view.load(QUrl.fromLocalFile(html_path))
            v.addWidget(self.holo_view)
        else:
            warn = QLabel("Holo map requires PyQt6-WebEngine (QtWebEngine). Install it to enable the 3D discovery map.")
            warn.setWordWrap(True)
            warn.setStyleSheet("color: rgba(200,220,255,0.75); padding: 8px;")
            v.addWidget(warn)

        self.discovery_tabs = QTabWidget()
        self.discovery_tabs.setObjectName("discoveryTabs")

        self.iface_table = QTableWidget(0, 5)
        self.iface_table.setHorizontalHeaderLabels(["Name", "State", "MAC", "IPv4", "IPv6"])
        self.iface_table.horizontalHeader().setStretchLastSection(True)
        self.iface_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.iface_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.iface_table.setAlternatingRowColors(True)

        self.ap_table = QTableWidget(0, 5)
        self.ap_table.setHorizontalHeaderLabels(["SSID", "BSSID", "CH", "Signal", "Security"])
        self.ap_table.horizontalHeader().setStretchLastSection(True)
        self.ap_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ap_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ap_table.setAlternatingRowColors(True)

        self.host_table = QTableWidget(0, 3)
        self.host_table.setHorizontalHeaderLabels(["IP", "MAC", "State"])
        self.host_table.horizontalHeader().setStretchLastSection(True)
        self.host_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.host_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.host_table.setAlternatingRowColors(True)

        self.discovery_tabs.addTab(self.iface_table, "Interfaces")
        self.discovery_tabs.addTab(self.ap_table, "Nearby Wi‑Fi")
        self.discovery_tabs.addTab(self.host_table, "Neighbors")
        v.addWidget(self.discovery_tabs)
        return wrapper

    def update_discovery(self, payload: dict) -> None:
        interfaces = payload.get("interfaces", []) or []
        aps = payload.get("aps", []) or []
        hosts = payload.get("hosts", []) or []

        def set_row(table: QTableWidget, r: int, c: int, value: str) -> None:
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(r, c, item)

        self.iface_table.setRowCount(len(interfaces))
        for r, it in enumerate(interfaces):
            set_row(self.iface_table, r, 0, str(it.get("name", "")))
            set_row(self.iface_table, r, 1, str(it.get("state", "")))
            set_row(self.iface_table, r, 2, str(it.get("mac", "")))
            ipv4 = it.get("ipv4") or []
            ipv6 = it.get("ipv6") or []
            set_row(self.iface_table, r, 3, ", ".join(ipv4) if isinstance(ipv4, list) else str(ipv4))
            set_row(self.iface_table, r, 4, ", ".join(ipv6) if isinstance(ipv6, list) else str(ipv6))

        self.ap_table.setRowCount(len(aps))
        for r, ap in enumerate(aps):
            set_row(self.ap_table, r, 0, str(ap.get("ssid", "")))
            set_row(self.ap_table, r, 1, str(ap.get("bssid", "")))
            set_row(self.ap_table, r, 2, str(ap.get("chan", "")))
            set_row(self.ap_table, r, 3, f"{ap.get('signal', '')}%")
            set_row(self.ap_table, r, 4, str(ap.get("security", "")))

        self.host_table.setRowCount(len(hosts))
        for r, h in enumerate(hosts):
            set_row(self.host_table, r, 0, str(h.get("ip", "")))
            set_row(self.host_table, r, 1, str(h.get("mac", "")))
            set_row(self.host_table, r, 2, str(h.get("state", "")))

        if self.holo_view is not None:
            try:
                js = "window.netNinjaUpdate(%s);" % json.dumps({"interfaces": interfaces, "aps": aps, "hosts": hosts}, ensure_ascii=False)
                self.holo_view.page().runJavaScript(js)
            except Exception:
                pass


    def build_genome_group(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Sequencing Protocol"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.scan_presets.keys()))
        layout.addWidget(self.preset_combo)
        layout.addWidget(create_glowing_button("Initiate Sequencing", self.run_selected_preset))
        layout.addStretch()
        return container

    def build_sequencing_group(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(12)

        grid.addWidget(QLabel("Initiate genome sequencing across common vectors."), 0, 0, 1, 2)
        quick_button = create_glowing_button("Rapid Sequencing (nmap -T4 -F)", self.run_quick)
        grid.addWidget(quick_button, 1, 0)

        full_button = create_glowing_button("Full Genome Scan (-sS -sV -A -p-)", self.run_full)
        grid.addWidget(full_button, 1, 1)

        stealth_button = create_glowing_button("Stealth Vector (-sS -T2 -f)", self.run_stealth)
        grid.addWidget(stealth_button, 2, 0)

        udp_button = create_glowing_button("UDP Vector Scan (--top-ports 100)", self.run_udp)
        grid.addWidget(udp_button, 2, 1)

        vuln_button = create_glowing_button("Vulnerability Assay (--script vuln)", self.run_vuln)
        grid.addWidget(vuln_button, 3, 0)

        service_button = create_glowing_button("Service Fingerprinting (-sV)", self.run_service)
        grid.addWidget(service_button, 3, 1)

        return container

    def build_mass_group(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        layout.addWidget(QLabel("Specialized scans"), 0, 0, 1, 2)

        masscan_btn = create_glowing_button("Masscan (fast ports)", self.run_masscan)
        layout.addWidget(masscan_btn, 1, 0)

        rustscan_btn = create_glowing_button("Rustscan + nmap", self.run_rustscan)
        layout.addWidget(rustscan_btn, 1, 1)
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
        cmd = f"nmap -T4 -F {quote(target)}"
        self.executor(cmd, "Quick scan", target=target)

    def run_full(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -sV -sC -A -p- {quote(target)}"
        self.executor(cmd, "Full scan", target=target)

    def run_stealth(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -T2 -f {quote(target)}"
        self.executor(cmd, "Stealth scan", target=target)

    def run_udp(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sU --top-ports 100 {quote(target)}"
        self.executor(cmd, "UDP scan", target=target)

    def run_vuln(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap --script vuln {quote(target)}"
        self.executor(cmd, "Vuln scan", target=target)

    def run_service(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap -sV {quote(target)}"
        self.executor(cmd, "Service scan", target=target)

    def run_masscan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        if not self.require_authorization("Masscan sweep"):
            self.output_log.appendPlainText("[info] Masscan cancelled (authorization phrase not provided)")
            return
        cmd = f"sudo masscan -p1-65535 {quote(target)} --rate 10000"
        self.executor(cmd, "Masscan sweep", target=target)

    def run_rustscan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"rustscan -a {quote(target)} --ulimit 5000 -- -sV"
        self.executor(cmd, "Rustscan belt", target=target)


class ReconTab(CategoryTab):
    """RECON tab covering discovery and enumeration."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.target_field = TargetField("Subnet/host")
        main_window.register_target_field(self.target_field)
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        self.discovery_options = [
            ("Ping sweep (nmap -sn)", "nmap -sn {target}", "Ping sweep"),
            ("Netdiscover", "sudo netdiscover -r {target}", "Netdiscover"),
            ("ARP scan (arp-scan -l)", "sudo arp-scan -l", "ARP scan"),
        ]
        self.enum_options = [
            ("DNS enum (dnsenum)", "dnsenum {target}", "DNS enumeration"),
            ("DNS recon (dnsrecon)", "dnsrecon -d {target}", "DNS recon"),
            ("SSL scan (sslscan)", "sslscan {target}", "SSL scan"),
            ("SSLyze (sslyze)", "sslyze --regular {target}", "SSLyze"),
            ("SNMP sweep (onesixtyone)", "onesixtyone {target}", "SNMP sweep"),
            ("SMB enum (enum4linux)", "enum4linux -a {target}", "SMB enumeration"),
        ]
        self.add_panel("Target Scope", target_wrap, "Define the subnet/host to interrogate.", column_span=2)
        self.add_panel("Network Discovery", self.create_discovery_group())
        self.add_panel("Enumeration", self.create_enum_group())

    def create_discovery_group(self) -> QGroupBox:
        group = self.add_group("Network Discovery", "ARP, ping, and discovery scans.")
        btn_layout = QGridLayout()
        btn_layout.setSpacing(6)

        for idx, (label, template, desc) in enumerate(self.discovery_options):
            button = create_glowing_button(
                label, lambda template=template, desc=desc: self.run_discovery(template, desc)
            )
            btn_layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(btn_layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Quick discovery selection"))
        self.discovery_combo = QComboBox()
        self.discovery_combo.addItems([label for label, *_ in self.discovery_options])
        drop_layout.addWidget(self.discovery_combo)
        drop_layout.addWidget(create_glowing_button("Execute", self.run_discovery_dropdown))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def create_enum_group(self) -> QGroupBox:
        group = self.add_group("Enumeration", "DNS, SSL/TLS, SNMP, and SMB mapping.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.enum_options):
            button = create_glowing_button(
                label, lambda template=template, desc=desc: self.run_enum(template, desc)
            )
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Enumeration quick-run"))
        self.enum_combo = QComboBox()
        self.enum_combo.addItems([label for label, *_ in self.enum_options])
        drop_layout.addWidget(self.enum_combo)
        drop_layout.addWidget(create_glowing_button("Run", self.run_enum_dropdown))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def run_discovery(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if "target" in template and not target:
            QMessageBox.warning(self, "Target missing", "Provide an IP/host/CIDR.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target or "broadcast")

    def run_enum(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a DNS name or host.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target)

    def run_discovery_dropdown(self) -> None:
        idx = self.discovery_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.discovery_options[idx]
        self.run_discovery(template, desc)

    def run_enum_dropdown(self) -> None:
        idx = self.enum_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.enum_options[idx]
        self.run_enum(template, desc)


class WirelessTab(CategoryTab):
    """WIRELESS tab for interface control, reconnaissance, and cracking."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.executor = executor
        self.iface_field = TargetField("Wireless interface", share_history=False)
        main_window.register_target_field(self.iface_field)
        self.bssid_field = TargetField("Target BSSID", share_history=True)
        # Register BSSID field with the main window for shared history
        if main_window:
            main_window.register_bssid_field(self.bssid_field)
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel")
        self.attack_combo = QComboBox()
        self.attack_combo.addItems(
            ["Deauth attack", "WPS attack (reaver)", "Handshake capture"]
        )
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel"))
        channel_layout.addWidget(self.channel_input)
        target_box = QWidget()
        target_layout = QVBoxLayout(target_box)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.iface_field)
        target_layout.addWidget(self.bssid_field)
        target_layout.addLayout(channel_layout)

        self.add_panel("Interfaces & Targets", target_box, "Select interfaces, BSSIDs, and channels.", column_span=2)
        self.add_panel("Interface Control", self.build_interface_group())
        self.add_panel("Recon & Capture", self.build_recon_group())
        self.add_panel("Attacks", self.build_attacks_group())
        self.add_panel("Cracking & Conversion", self.build_cracking_group())

    def build_interface_group(self) -> QGroupBox:
        group = self.add_group("Interface control", "")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        enable_btn = create_glowing_button("Enable monitor mode", self.enable_monitor)
        disable_btn = create_glowing_button("Disable monitor mode", self.disable_monitor)
        refresh_btn = create_glowing_button("Refresh interfaces", self.refresh_interfaces)
        layout.addWidget(enable_btn, 0, 0)
        layout.addWidget(disable_btn, 0, 1)
        layout.addWidget(refresh_btn, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        return group

    def build_recon_group(self) -> QGroupBox:
        group = self.add_group("Recon & capture", "airodump-ng, bettercap, wifite.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        airodump = create_glowing_button("Run airodump-ng (10s)", self.run_airodump)
        bettercap = create_glowing_button("Bettercap capture", self.run_bettercap)
        wifite = create_glowing_button("Start wifite (auto)", self.run_wifite)
        layout.addWidget(airodump, 0, 0)
        layout.addWidget(bettercap, 0, 1)
        layout.addWidget(wifite, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        return group

    def build_attacks_group(self) -> QGroupBox:
        group = self.add_group("Attacks", "Deauth, WPS, and handshake capture.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        deauth_btn = create_glowing_button("Deauth attack", self.deauth_attack)
        wps_btn = create_glowing_button("WPS attack (reaver)", self.wps_attack)
        handshake_btn = create_glowing_button("Capture handshake", self.capture_handshake)
        layout.addWidget(deauth_btn, 0, 0)
        layout.addWidget(wps_btn, 0, 1)
        layout.addWidget(handshake_btn, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Attack preset"))
        drop_layout.addWidget(self.attack_combo)
        drop_layout.addWidget(create_glowing_button("Launch attack", self.run_selected_wireless_attack))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def build_cracking_group(self) -> QGroupBox:
        group = self.add_group("Cracking & conversion", "Aircrack-ng / Hashcat helpers.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        aircrack_btn = create_glowing_button("Crack with aircrack-ng", self.run_aircrack)
        hashcat_btn = create_glowing_button("Crack with hashcat", self.run_hashcat)
        convert_btn = create_glowing_button("Convert .cap → .hc22000", self.convert_handshake)
        layout.addWidget(aircrack_btn, 0, 0)
        layout.addWidget(hashcat_btn, 0, 1)
        layout.addWidget(convert_btn, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        return group

    def iface(self) -> Optional[str]:
        value = self.iface_field.value()
        if not value:
            QMessageBox.warning(self, "Interface missing", "Select a wireless interface.")
            return None
        return value

    def refresh_interfaces(self) -> None:
        """Populate the interface selector with available wireless or network interfaces."""
        # SECURITY FIX: Avoid shell=True by using a proper pipeline
        try:
            p1 = subprocess.Popen(["iw", "dev"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["awk", "/Interface/ {print $2}"], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            output, _ = p2.communicate()
            interfaces = [line.strip() for line in output.splitlines() if line.strip()]
        except (FileNotFoundError, Exception):
            interfaces = []

        # Fallback: enumerate all network interfaces if none found
        if not interfaces:
            try:
                candidates = os.listdir('/sys/class/net')
                interfaces = [iface for iface in candidates if iface != 'lo']
            except Exception:
                interfaces = []
        
        self.iface_field.combo.clear()
        if interfaces:
            self.iface_field.combo.addItems(interfaces)
        summary = ", ".join(interfaces) if interfaces else "no network interfaces detected"
        if self.main_window:
            self.main_window.output_log.appendPlainText(f"[info] Interfaces refreshed: {summary}")

    def enable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng start {quote(iface)}"
        self.executor(cmd, "Enable monitor mode", target=iface)

    def disable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng stop {quote(iface)}"
        self.executor(cmd, "Disable monitor", target=iface)

    def run_airodump(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo timeout 15 airodump-ng {quote(iface)}"
        self.executor(cmd, "airodump-ng scan", target=iface)

    def run_bettercap(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo bettercap -iface {quote(iface)} -eval 'set arp.spoof.fullduplex true; net.sniff on'"
        self.executor(cmd, "Bettercap session", target=iface)

    def run_wifite(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo wifite -i {quote(iface)} --kill"
        self.executor(cmd, "Wifite attack", target=iface)

    def deauth_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or "FF:FF:FF:FF:FF:FF"
        if not self.require_authorization("Deauth attack"):
            self.output_log.appendPlainText("[info] Deauth attack cancelled (authorization phrase not provided)")
            return
        if self.main_window and self.bssid_field.value():
            self.main_window.add_bssid_history(self.bssid_field.value())
        cmd = f"sudo aireplay-ng --deauth 10 -a {quote(target)} {quote(iface)}"
        self.executor(cmd, "Deauth", target=iface)

    def wps_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or ""
        if not target:
            QMessageBox.warning(self, "BSSID required", "Provide a target BSSID for WPS attacks.")
            return
        if not self.require_authorization("WPS attack"):
            self.output_log.appendPlainText("[info] WPS attack cancelled (authorization phrase not provided)")
            return
        if self.main_window:
            self.main_window.add_bssid_history(target)
        channel = self.channel_input.text().strip()
        channel_arg = f"-c {quote(channel)}" if channel else ""
        cmd = f"sudo reaver -i {quote(iface)} -b {quote(target)} {channel_arg} -N -vv"
        self.executor(cmd, "WPS attack (reaver)", target=target)

    def capture_handshake(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value()
        if not target:
            QMessageBox.warning(self, "BSSID missing", "Provide the target BSSID for capture.")
            return
        if not self.require_authorization("Handshake capture"):
            self.output_log.appendPlainText("[info] Handshake capture cancelled (authorization phrase not provided)")
            return
        if self.main_window:
            self.main_window.add_bssid_history(target)
        channel = self.channel_input.text().strip()
        channel_arg = f"-c {quote(channel)}" if channel else ""
        cmd = f"sudo timeout 20 airodump-ng --bssid {quote(target)} {channel_arg} -w /tmp/handshake {quote(iface)}"
        self.executor(cmd, "Handshake capture", target=target)

    def run_aircrack(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/capture.cap")
        if not ok or not capfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"aircrack-ng -w {quote(wordlist)} {quote(capfile)}"
        self.executor(cmd, "Aircrack-ng", target=capfile)

    def run_hashcat(self) -> None:
        hashfile, ok = self.request_input("Hash/Capture file", "/tmp/hash.hc22000")
        if not ok or not hashfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"hashcat -m 22000 -a 0 {quote(hashfile)} {quote(wordlist)} --status --potfile-path /tmp/hashcat.pot"
        self.executor(cmd, "Hashcat", target=hashfile)

    def convert_handshake(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/handshake.cap")
        if not ok or not capfile:
            return
        cmd = f"hcxpcapngtool -o {quote(capfile)}.hc22000 {quote(capfile)}"
        self.executor(cmd, "Convert handshake", target=capfile)

    def run_selected_wireless_attack(self) -> None:
        choice = self.attack_combo.currentText()
        if choice == "Deauth attack":
            self.deauth_attack()
        elif choice == "WPS attack (reaver)":
            self.wps_attack()
        elif choice == "Handshake capture":
            self.capture_handshake()

    def request_input(self, prompt: str, default: str = "") -> Tuple[str, bool]:
        value, ok = QInputDialog.getText(self, "Input required", prompt, text=default)
        return value, ok


class WebTab(CategoryTab):
    """WEB tab for scanners and injection tools."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.target_field = TargetField("URL / Domain")
        main_window.register_target_field(self.target_field)
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        self.web_scanners = [
            ("SQLmap", "sqlmap -u {target} --batch", "SQL injection"),
            ("Nikto", "nikto -host {target}", "Web server vuln scan"),
            ("Nuclei", "nuclei -u {target}", "Template-based scans"),
            ("XSStrike", "xsstrike {target}", "XSS fuzzing"),
            ("Commix", "commix -u {target} --batch", "Command injection"),
        ]
        self.dir_tools = [
            ("Gobuster", "gobuster dir -u {target} -w /usr/share/wordlists/raft.txt"),
            ("Dirb", "dirb {target} /usr/share/wordlists/raft.txt"),
            ("Feroxbuster", "feroxbuster -u {target} -w /usr/share/wordlists/raft.txt"),
        ]
        self.add_panel("Target URL / Domain", target_wrap, "Scope for scanners and brute-force", column_span=2)
        self.add_panel("Scanners & Injection", self.build_web_tools_group())
        self.add_panel("Directory Brute-force", self.build_directory_group())

    def build_web_tools_group(self) -> QGroupBox:
        group = self.add_group("Scanners & injection", "SQLmap, Nikto, nuclei, Commix, XSStrike.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.web_scanners):
            button = create_glowing_button(label, lambda t=template, d=desc: self.run_web_tool(t, d))
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Select scanner"))
        self.web_combo = QComboBox()
        self.web_combo.addItems([label for label, *_ in self.web_scanners])
        drop_layout.addWidget(self.web_combo)
        drop_layout.addWidget(create_glowing_button("Launch", self.run_web_combo))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def build_directory_group(self) -> QGroupBox:
        group = self.add_group("Directory brute-force", "Gobuster, Dirb, Feroxbuster.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        for idx, (label, template) in enumerate(self.dir_tools):
            button = create_glowing_button(label, lambda t=template: self.run_dir_tool(t))
            layout.addWidget(button, idx // 2, idx % 2)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Directory fuzz"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItems([label for label, *_ in self.dir_tools])
        drop_layout.addWidget(self.dir_combo)
        drop_layout.addWidget(create_glowing_button("Start", self.run_dir_combo))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def run_web_tool(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a URL before running.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target)

    def run_dir_tool(self, template: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a target URL.")
            return
        command = template.format(target=quote(target))
        self.executor(command, "Directory bruteforce", target=target)

    def run_web_combo(self) -> None:
        idx = self.web_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.web_scanners[idx]
        self.run_web_tool(template, desc)

    def run_dir_combo(self) -> None:
        idx = self.dir_combo.currentIndex()
        if idx < 0:
            return
        _, template = self.dir_tools[idx]
        self.run_dir_tool(template)


class NetReaperGui(QWidget):
    """Main container that stitches tabs, logs, and history."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetReaper Command Center")
        self.setMinimumSize(1200, 720)
        self.session_id = uuid4().hex[:8].upper()
        self.ingress_online = False
        self.target_fields: List[TargetField] = []
        self.target_history: List[str] = []
        self.bssid_fields: List[TargetField] = []
        self.bssid_history: List[str] = []
        self.active_threads: List[CommandThread] = []
        self.wiring_flags = {}
        self.lite_mode = False
        self.custom_wordlist = ""

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
        refresh_status_action = QAction("Show status", self)
        refresh_status_action.triggered.connect(lambda: self.execute_command("netreaper status", "Status"))
        self.toolbar.addAction(refresh_status_action)

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

        wordlist_action = QAction("Select wordlist", self)
        wordlist_action.triggered.connect(self.select_wordlist)
        self.toolbar.addAction(wordlist_action)
        main_layout.addWidget(self.toolbar)

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

        self.scan_tab = ScanTab(self.execute_command, self)
        self.recon_tab = ReconTab(self.execute_command, self)
        self.wireless_tab = WirelessTab(self.execute_command, self)
        self.web_tab = WebTab(self.execute_command, self)
        self.wizard_tab = WizardTab(self.execute_command, self)
        self.jobs_tab = JobsTab(self)

        wizard_page = self._wrap_in_workspace("Automation Wizards", self.wizard_tab)
        jobs_page = self._wrap_in_workspace("Containment Logs", self.jobs_tab)

        self.pages = [
            ("Scan", self.scan_tab),
            ("Recon", self.recon_tab),
            ("Wireless", self.wireless_tab),
            ("Web", self.web_tab),
            ("Wizards", wizard_page),
            ("Jobs", jobs_page),
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
        self.reaper_header.add_nav_button("Wireless", lambda: self.navigate_to("Wireless"))
        self.reaper_header.add_nav_button("Web", lambda: self.navigate_to("Web"))
        self.reaper_header.add_nav_button("Wizards", lambda: self.navigate_to("Wizards"))
        self.reaper_header.add_nav_button("Jobs", lambda: self.navigate_to("Jobs"))

        self._load_target_history()
        for field in self.target_fields:
            field.set_history(self.target_history)

        self._load_bssid_history()
        if self.bssid_history:
            for bssid_field in self.bssid_fields:
                bssid_field.set_history(self.bssid_history)

        self.hero_timer = QTimer(self)
        self.hero_timer.timeout.connect(self.refresh_reaper_header)
        self.hero_timer.start(1000)
        self.refresh_reaper_header()
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
        self.cmd_input.setPlaceholderText("Enter command")
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
            else:
                current = field.value()
                if current:
                    self.target_history.append(current)
                    field.set_history(self.target_history)

    def start_discovery(self) -> None:
        """Run interface/Wi‑Fi/neighbor discovery and update Scan tab + holo map."""
        # Guard: ensure scan_tab exists
        scan_tab = getattr(self, "scan_tab", None)
        if scan_tab is None or not hasattr(scan_tab, "update_discovery"):
            QMessageBox.warning(self, "Discovery unavailable", "Scan tab is not ready for discovery updates.")
            return

        # Show progress in the operations console and keep UI responsive
        self.output_log.appendPlainText("[DISCOVERY] Starting network discovery…")
        self.status_label.setText("Discovery: running…")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # indeterminate

        self._discovery_thread = DiscoveryThread(rescan_wifi=True, parent=self)
        self._discovery_thread.log.connect(lambda line: self.output_log.appendPlainText(line))
        def on_result(payload: dict) -> None:
            self.progress.setVisible(False)
            self.progress.setRange(0, 100)
            errs = payload.get("errors", []) or []
            if errs:
                self.output_log.appendPlainText("[DISCOVERY] Completed with warnings:")
                for e in errs:
                    self.output_log.appendPlainText(f"  - {e}")
                self.status_label.setText("Discovery: completed (warnings)")
            else:
                self.output_log.appendPlainText("[DISCOVERY] Completed successfully.")
                self.status_label.setText("Discovery: completed")

            try:
                scan_tab.update_discovery(payload)
            except Exception as ex:
                self.output_log.appendPlainText(f"[DISCOVERY] UI update error: {ex!r}")

        self._discovery_thread.result.connect(on_result)
        self._discovery_thread.finished.connect(lambda: self.progress.setVisible(False))
        self._discovery_thread.start()



    def add_target_history(self, target: str) -> None:
        if not target:
            return
        history = [target] + [t for t in self.target_history if t != target]
        self.target_history = history[:20]
        for field in self.target_fields:
            field.set_history(history)

    def register_bssid_field(self, field: TargetField) -> None:
        if not field.share_history:
            return
        if field not in self.bssid_fields:
            self.bssid_fields.append(field)
            if self.bssid_history:
                field.set_history(self.bssid_history)
            else:
                current = field.value()
                if current:
                    self.bssid_history.append(current)
                    field.set_history(self.bssid_history)

    def add_bssid_history(self, bssid: str) -> None:
        if not bssid:
            return
        history = [bssid] + [b for b in self.bssid_history if b != bssid]
        self.bssid_history = history[:20]
        for field in self.bssid_fields:
            field.set_history(history)
        history_path = getattr(self, "_bssid_history_path", "")
        if history_path:
            try:
                os.makedirs(os.path.dirname(history_path), exist_ok=True)
                with open(history_path, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(self.bssid_history))
            except OSError:
                pass

    def _load_target_history(self) -> None:
        history_paths = [
            os.path.expanduser("~/.netreaper/history/scans.log"),
            os.path.expanduser("~/.netreaper/history/targets.log"),
        ]
        loaded: List[str] = []
        for path in history_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            target = line.strip().split()[0] if line.strip() else ""
                            if target and target not in loaded:
                                loaded.append(target)
                except OSError:
                    continue
        self.target_history = loaded[:20]

    def _load_bssid_history(self) -> None:
        self._bssid_history_path = os.path.expanduser("~/.netreaper/history/bssid.log")
        entries: List[str] = []
        try:
            if os.path.exists(self._bssid_history_path):
                with open(self._bssid_history_path, "r", encoding="utf-8") as fh:
                    entries = [line.strip() for line in fh if line.strip()]
        except OSError:
            entries = []
        self.bssid_history = entries[:20]

    def execute_command(self, command: str, description: str, target: Optional[str] = None) -> None:
        """Execute a shell command with security hardening."""
        try:
            cmd_tokens = shlex.split(command)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid command", f"Command parsing failed: {e}")
            return
        
        if not cmd_tokens:
            QMessageBox.warning(self, "Empty command", "No command provided")
            return
        
        tool = cmd_tokens[0] if cmd_tokens[0] != 'sudo' else cmd_tokens[1]
        
        tool_path = shutil.which(tool)
        if tool_path is None:
            QMessageBox.warning(self, "Tool missing", f"The command '{tool}' is not in PATH.")
            return
        if not os.access(tool_path, os.X_OK):
            QMessageBox.warning(self, "Tool not executable", f"'{tool}' is not executable.")
            return
        
        actual_command = command
        if self.lite_mode and not command.startswith("NR_LITE_MODE="):
            actual_command = f"NR_LITE_MODE=1 {command}"
        
        if hasattr(self, "custom_wordlist") and self.custom_wordlist:
            actual_command = f"DEFAULT_WORDLIST={shlex.quote(self.custom_wordlist)} {actual_command}"
        
        sudo_password = None
        if cmd_tokens[0] == "sudo":
            password, ok = QInputDialog.getText(self, "Sudo Password", "Enter password for sudo:", QLineEdit.EchoMode.Password)
            if not ok:
                self.output_log.appendPlainText("[info] Sudo command cancelled by user.")
                self.output_status_label.setText("Status: idle (sudo cancelled)")
                return
            sudo_password = password
        
        log_command = self.sanitize_command_for_display(actual_command)
        self.current_command_label.setText(f"Command: {log_command}")
        self.output_status_label.setText(f"Status: running ({description})")
        if hasattr(self, "output_panel"):
            self.output_panel.set_status("#5ad6ff")
        self.output_log.appendPlainText(f"[{description}] $ {log_command}")
        
        if target:
            self.add_target_history(target)
        
        thread = CommandThread(actual_command, sudo_password=sudo_password, sanitize_output=True)
        thread.output.connect(self.output_log.appendPlainText)
        thread.finished.connect(self.on_finished)
        thread.finished.connect(lambda _: self.resize_log())
        self.active_threads.append(thread)
        thread.finished.connect(lambda code, thr=thread: self.cleanup_thread(thr))
        self.ingress_online = True
        self.refresh_reaper_header()
        thread.start()

        item = QListWidgetItem(f"{description}: {log_command}")
        item.setData(Qt.ItemDataRole.UserRole, actual_command)
        self.history_list.addItem(item)
        self.history_panel.set_status("#5ad6ff")
    
    def sanitize_command_for_display(self, command: str) -> str:
        """Redact sensitive information from commands before logging or displaying."""
        return sanitize_command_for_display(command)

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
        if hasattr(self, "output_panel"):
            self.output_panel.set_status(color)
        if hasattr(self, "history_panel"):
            self.history_panel.set_status(color)

    def clear_log(self) -> None:
        self.output_log.clear()
        self.output_status_label.setText("Status: idle")
        self.current_command_label.setText("Command: none")
        if hasattr(self, "output_panel"):
            self.output_panel.set_status("#3dd598")
        if hasattr(self, "history_panel"):
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
        if command:
            self.execute_command(command, "Re-run")

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
            self.output_log.appendPlainText(f"> {cmd}")
            self.execute_command(cmd, "Manual Command")
            self.cmd_input.clear()

    def stop_all_tasks(self) -> None:
        """Terminate all running command threads and clear the active thread list."""
        if not self.active_threads:
            self.output_log.appendPlainText("[info] No active tasks to stop")
            return
        self.output_log.appendPlainText("[info] Stopping all active tasks...")
        for thread in list(self.active_threads):
            try:
                thread.terminate()
            except Exception:
                pass
        self.active_threads.clear()
        self.ingress_online = False
        self.refresh_reaper_header()
        self.output_status_label.setText("Status: stopped")
        if hasattr(self, "output_panel"):
            self.output_panel.set_status("#ff7b7b")
        if hasattr(self, "history_panel"):
            self.history_panel.set_status("#ff7b7b")

    def toggle_lite_mode(self, enabled: bool) -> None:
        """Toggle Lite mode on or off. When enabled, commands run in low-resource mode."""
        self.lite_mode = bool(enabled)
        mode = "enabled" if self.lite_mode else "disabled"
        if hasattr(self, "hud_panel") and self.hud_panel:
            if self.lite_mode:
                self.hud_panel.status_label.setText("CONTAINMENT STATUS: LITE MODE")
            else:
                self.hud_panel.status_label.setText("CONTAINMENT STATUS: STANDBY")
        self.output_log.appendPlainText(f"[info] Lite mode {mode}")
        self.output_status_label.setText(f"Status: lite mode {mode}")
        if hasattr(self, "output_panel"):
            self.output_panel.set_status("#5ad6ff" if self.lite_mode else "#3dd598")

    def edit_config(self) -> None:
        """Open a simple editor for the user's configuration file (~/.netreaper/config)."""
        from PyQt6.QtWidgets import QDialog
        config_path = os.path.expanduser("~/.netreaper/config")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
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

    def select_wordlist(self) -> None:
        """Prompt the user to select a custom wordlist for password attacks."""
        path, _ = QFileDialog.getOpenFileName(self, "Select wordlist", os.path.expanduser("~/"), "Wordlists (*.txt *.lst *.*)")
        if path:
            self.custom_wordlist = path
            QMessageBox.information(self, "Wordlist selected", f"Using custom wordlist: {path}")


def main() -> None:
    app = QApplication(sys.argv)
    apply_bio_theme(app)
    window = QWidget()
    layout = QVBoxLayout(window)
    gui = NetReaperGui()
    layout.addWidget(gui)
    window.setWindowTitle("NetReaper Command Center")
    window.resize(1280, 1000)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
