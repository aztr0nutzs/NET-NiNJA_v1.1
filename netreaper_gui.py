#!/usr/bin/env python3
"""
NetReaper GUI — Cyberpunk dark native toolkit interface.

Reimplements the CLI SCAN, RECON, WIRELESS, and WEB flows using PyQt6 so the
toolset is fully usable from a windowed interface without losing the Brass
hammer controls that security engineers expect.
"""

from __future__ import annotations


import os
import sys

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

import shlex
import json
import subprocess
import sys
import time
import platform
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, QEventLoop, Qt, pyqtSignal, QUrl, QSettings, QByteArray, QObject, QThread

import shutil  # For checking tool availability

import os  # Added for interface discovery and history loading
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
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
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QAbstractItemView,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QProgressBar,
    QTabWidget,
)


from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
from PyQt6.QtMultimediaWidgets import QVideoWidget
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
from capabilities import detect_capabilities
from camera_ip import DiscoveredCamera, guess_rtsp_urls, ws_discover
from providers import get_provider
from providers.base import HostRecord, InterfaceRecord, NeighborRecord, RouteRecord, SocketRecord, WifiAPRecord
from job_pipeline import ExecutionResult, JobManager, JobSpec




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
            print("[warn] Glow animation easing not available")
    animation.start()
    widget._glow_animation = animation


def create_glowing_button(text: str, callback, *, enabled: bool = True, tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    button.clicked.connect(lambda checked=False, cb=callback: cb())
    button.setEnabled(enabled)
    if tooltip:
        button.setToolTip(tooltip)
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


class ScaledPixmapLabel(QLabel):
    """QLabel that scales an original pixmap to the widget size (smooth), used for pixel-perfect header strips."""

    def __init__(self, path: str, fixed_height: int | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._orig = QPixmap(path)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if fixed_height is not None:
            self.setFixedHeight(fixed_height)
        # paint initial
        self._rescale()

    def _rescale(self) -> None:
        if self._orig.isNull():
            self.clear()
            return
        size = self.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        self.setPixmap(self._orig.scaled(size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()



class ReaperHeader(QFrame):
    """Pixel-faithful NET-NiNJA header.

    This header is rendered from a single composite reference image (imgs/header_reference.png).
    No layout math, no font drift, no QSS drift — what you see is exactly the image.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ReaperHeader")
        self.setFrameShape(QFrame.NoFrame)

        ref_path = resource_path("imgs/header_reference.png")
        self._pix = QPixmap(ref_path)

        # Hard fail early with a clear message if the asset is missing.
        if self._pix.isNull():
            raise FileNotFoundError(f"Missing header reference image: {ref_path}")

        # Lock height to the exact reference height. Width is handled via window sizing/min width.
        self.setFixedHeight(self._pix.height())
        self.setMinimumWidth(self._pix.width())

    def reference_size(self) -> QSize:
        return self._pix.size()

    def sizeHint(self) -> QSize:
        return self._pix.size()

    def paintEvent(self, event) -> None:
        # Draw the reference image at (0,0) without scaling so it stays pixel-perfect.
        # Any extra space is simply filled with black.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        painter.drawPixmap(0, 0, self._pix)
        painter.end()

class TargetField(QWidget):
    """Reusable target selector with editable combo box."""

    scan_requested = pyqtSignal(object)

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
        self.scan_btn.clicked.connect(lambda: self.scan_requested.emit(self))
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

    def run_job(self, job: JobSpec) -> None:
        if self.main_window and hasattr(self.main_window, "job_manager"):
            self.main_window.job_manager.run_job(job)

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
    """Structured job history, diagnostics export, and raw output viewer."""

    def __init__(self, job_manager: JobManager, save_diagnostics, run_self_test, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.job_manager = job_manager
        self._results_by_id: Dict[str, Dict[str, Any]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        action_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_jobs)
        save_button = QPushButton("Save Diagnostics")
        save_button.clicked.connect(save_diagnostics)
        self.self_test_button = QPushButton("Run Self Test")
        self.self_test_button.clicked.connect(run_self_test)
        action_row.addWidget(refresh_button)
        action_row.addWidget(save_button)
        action_row.addWidget(self.self_test_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.jobs_table = QTableWidget(0, 7)
        self.jobs_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Category", "Status", "Return", "Items", "Duration (s)"]
        )
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.jobs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.jobs_table.itemSelectionChanged.connect(self._on_job_selected)
        layout.addWidget(self.jobs_table, 2)

        detail_row = QHBoxLayout()
        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        detail_row.addWidget(self.summary_table, 2)

        self.raw_button = QPushButton("View Raw Output")
        self.raw_button.clicked.connect(self._show_raw_output)
        detail_controls = QVBoxLayout()
        detail_controls.addWidget(self.raw_button)
        detail_controls.addStretch()
        detail_row.addLayout(detail_controls, 0)
        layout.addLayout(detail_row, 1)

        self.job_manager.result_emitted.connect(self._on_job_result)
        self.refresh_jobs()

    def refresh_jobs(self) -> None:
        self.jobs_table.setRowCount(0)
        for result in self.job_manager.job_history:
            self._add_job_row(result)

    def _on_job_result(self, result: Dict[str, Any]) -> None:
        self._add_job_row(result)

    def _add_job_row(self, result: Dict[str, Any]) -> None:
        job_id = result.get("job_id", "")
        self._results_by_id[job_id] = result
        row = self.jobs_table.rowCount()
        self.jobs_table.insertRow(row)
        self.jobs_table.setItem(row, 0, QTableWidgetItem(job_id))
        self.jobs_table.setItem(row, 1, QTableWidgetItem(result.get("name", "")))
        self.jobs_table.setItem(row, 2, QTableWidgetItem(result.get("category", "")))
        self.jobs_table.setItem(row, 3, QTableWidgetItem(result.get("status", "")))
        self.jobs_table.setItem(row, 4, QTableWidgetItem(str(result.get("returncode", ""))))
        items = result.get("payload", {}).get("items", [])
        self.jobs_table.setItem(row, 5, QTableWidgetItem(str(len(items))))
        duration = result.get("elapsed", 0.0)
        self.jobs_table.setItem(row, 6, QTableWidgetItem(f"{duration:.2f}"))

    def _on_job_selected(self) -> None:
        selected = self.jobs_table.selectedItems()
        if not selected:
            return
        job_id = selected[0].text()
        result = self._results_by_id.get(job_id)
        if not result:
            return
        summary = result.get("summary", {}) or {}
        self.summary_table.setRowCount(len(summary))
        for row, (key, value) in enumerate(summary.items()):
            self.summary_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _show_raw_output(self) -> None:
        selected = self.jobs_table.selectedItems()
        if not selected:
            return
        job_id = selected[0].text()
        result = self._results_by_id.get(job_id, {})
        raw = result.get("raw", {})
        stdout_lines = raw.get("stdout", [])
        stderr_lines = raw.get("stderr", [])
        text = []
        if stdout_lines:
            text.append("STDOUT:")
            text.extend(stdout_lines)
        if stderr_lines:
            text.append("")
            text.append("STDERR:")
            text.extend(stderr_lines)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Raw Output: {job_id}")
        layout = QVBoxLayout(dialog)
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText("\n".join(text))
        layout.addWidget(editor)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.resize(720, 520)
        dialog.exec()



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
        self.target_field.scan_requested.connect(lambda field: self.main_window.scan_targets_for_field(field))
        if self.main_window:
            self.main_window.guard_button(self.target_field.scan_btn, feature_flag="can_list_interfaces")
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
        if self.main_window:
            self.main_window.apply_feature_support(self.launch_button, "wizard.reaper_mode")
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
            out_path = os.path.join(tempfile.gettempdir(), f"reaper_{mode.lower().replace(' ', '_')}_{int(time.time())}.log")
            base_cmd += f" --output {shlex.quote(out_path)}"

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
        """Launch a wizard command using the unified job pipeline."""
        self.progress.setRange(0, 0)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.launch_button.setEnabled(False)

        if not self.main_window:
            self.status_label.setText("Wizard unavailable: no main window")
            self.progress.setVisible(False)
            self.launch_button.setEnabled(True)
            return

        job_id = self.main_window.submit_command_job(command, description, feature_key="wizard.reaper_mode")
        if not job_id:
            self.status_label.setText("Wizard start failed")
            self.progress.setVisible(False)
            self.launch_button.setEnabled(True)
            return

        def on_result(result: dict) -> None:
            if result.get("job_id") != job_id:
                return
            status = result.get("status", "failed")
            if status == "success":
                self.status_label.setText(f"{description} completed successfully.")
            else:
                self.status_label.setText(f"{description} failed.")
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            QTimer.singleShot(3000, lambda: self.progress.setVisible(False))
            self.launch_button.setEnabled(True)
            try:
                self.main_window.job_manager.result_emitted.disconnect(on_result)
            except Exception as exc:
                self.main_window._append_log_line(f"[wizard] Result disconnect failed: {exc}")

        self.main_window.job_manager.result_emitted.connect(on_result)

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
        self._settings = QSettings("NetNinja", "NetReaper")
        self.target_field = TargetField("Target")
        target_wrap = QWidget()
        target_layout = QVBoxLayout(target_wrap)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.addWidget(self.target_field)
        self.discovery_panel = self._build_discovery_panel()
        target_layout.addWidget(self.discovery_panel)

        # Ensure the Scan Networks button triggers structured discovery
        self.target_field.scan_requested.connect(lambda _field=None: self.main_window.start_discovery())
        self.main_window.guard_button(self.target_field.scan_btn, feature_flag="can_list_interfaces")
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

        self.discovery_splitter = QSplitter(Qt.Orientation.Vertical)
        self.discovery_splitter.setObjectName("discoverySplitter")
        self.discovery_splitter.setChildrenCollapsible(False)

        holo_container = QFrame()
        holo_container.setObjectName("holoMapContainer")
        holo_container.setMinimumHeight(280)
        holo_container.setMaximumHeight(520)
        holo_layout = QVBoxLayout(holo_container)
        holo_layout.setContentsMargins(0, 0, 0, 0)
        holo_layout.setSpacing(0)

        self.holo_view = None
        if QWebEngineView is not None:
            self.holo_view = QWebEngineView()
            self.holo_view.setObjectName("holoMapView")
            self.holo_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "holo_map", "index.html"))
            self.holo_view.load(QUrl.fromLocalFile(html_path))
            holo_layout.addWidget(self.holo_view)
        else:
            warn = QLabel("Holo map requires PyQt6-WebEngine (QtWebEngine). Install it to enable the 3D discovery map.")
            warn.setWordWrap(True)
            warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn.setStyleSheet("color: rgba(200,220,255,0.75); padding: 8px;")
            holo_layout.addWidget(warn)

        self.discovery_splitter.addWidget(holo_container)

        self.discovery_tabs = QTabWidget()
        self.discovery_tabs.setObjectName("discoveryTabs")
        self.discovery_tabs.setMinimumHeight(220)

        self.iface_table = QTableWidget(0, 6)
        self.iface_table.setHorizontalHeaderLabels(["Name", "State", "MAC", "IPv4", "IPv6", "Speed"])
        self.iface_table.horizontalHeader().setStretchLastSection(True)
        self.iface_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.iface_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.iface_table.setAlternatingRowColors(True)

        self.route_table = QTableWidget(0, 4)
        self.route_table.setHorizontalHeaderLabels(["Destination", "Gateway", "Interface", "Metric"])
        self.route_table.horizontalHeader().setStretchLastSection(True)
        self.route_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.route_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.route_table.setAlternatingRowColors(True)

        self.socket_table = QTableWidget(0, 6)
        self.socket_table.setHorizontalHeaderLabels(["Proto", "Local", "Remote", "State", "PID", "Process"])
        self.socket_table.horizontalHeader().setStretchLastSection(True)
        self.socket_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.socket_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.socket_table.setAlternatingRowColors(True)

        self.neighbor_table = QTableWidget(0, 4)
        self.neighbor_table.setHorizontalHeaderLabels(["IP", "MAC", "State", "Interface"])
        self.neighbor_table.horizontalHeader().setStretchLastSection(True)
        self.neighbor_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.neighbor_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.neighbor_table.setAlternatingRowColors(True)

        self.ap_table = QTableWidget(0, 5)
        self.ap_table.setHorizontalHeaderLabels(["SSID", "BSSID", "CH", "Signal", "Security"])
        self.ap_table.horizontalHeader().setStretchLastSection(True)
        self.ap_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ap_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ap_table.setAlternatingRowColors(True)

        self.host_table = QTableWidget(0, 4)
        self.host_table.setHorizontalHeaderLabels(["IP", "MAC", "State", "Source"])
        self.host_table.horizontalHeader().setStretchLastSection(True)
        self.host_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.host_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.host_table.setAlternatingRowColors(True)

        self.discovery_tabs.addTab(self.iface_table, "Interfaces")
        self.discovery_tabs.addTab(self.route_table, "Routes")
        self.discovery_tabs.addTab(self.socket_table, "Sockets")
        self.discovery_tabs.addTab(self.neighbor_table, "Neighbors")
        self.discovery_tabs.addTab(self.ap_table, "Nearby Wi-Fi")
        self.discovery_tabs.addTab(self.host_table, "Hosts")
        self.discovery_splitter.addWidget(self.discovery_tabs)
        v.addWidget(self.discovery_splitter)

        self.discovery_splitter.splitterMoved.connect(lambda _pos, _index: self._save_discovery_splitter_state())
        if not self._restore_discovery_splitter_state():
            self.discovery_splitter.setSizes([360, 520])
        return wrapper

    def _restore_discovery_splitter_state(self) -> bool:
        state = self._settings.value("discovery/splitter_state", None)
        if isinstance(state, QByteArray):
            return self.discovery_splitter.restoreState(state)
        if isinstance(state, (bytes, bytearray)):
            return self.discovery_splitter.restoreState(QByteArray(state))
        return False

    def _save_discovery_splitter_state(self) -> None:
        try:
            if hasattr(self, "discovery_splitter"):
                self._settings.setValue("discovery/splitter_state", self.discovery_splitter.saveState())
        except Exception as exc:
            if self.main_window:
                self.main_window._append_log_line(f"[settings] Splitter save failed: {exc}")

    def update_discovery(self, payload: dict) -> None:
        interfaces = payload.get("interfaces", []) or []
        routes = payload.get("routes", []) or []
        sockets = payload.get("sockets", []) or []
        neighbors = payload.get("neighbors", []) or []
        aps = payload.get("aps", []) or []
        hosts = payload.get("hosts", []) or []
        errors = payload.get("errors", []) or []

        def set_row(table: QTableWidget, r: int, c: int, value: str) -> None:
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(r, c, item)

        def get_value(item, attr, default=""):
            if isinstance(item, dict):
                return item.get(attr, default)
            return getattr(item, attr, default)

        self.iface_table.setRowCount(len(interfaces))
        for r, it in enumerate(interfaces):
            set_row(self.iface_table, r, 0, str(get_value(it, "name", "")))
            set_row(self.iface_table, r, 1, str(get_value(it, "state", "")))
            set_row(self.iface_table, r, 2, str(get_value(it, "mac", "")))
            ipv4 = get_value(it, "ipv4", []) or []
            ipv6 = get_value(it, "ipv6", []) or []
            set_row(self.iface_table, r, 3, ", ".join(ipv4) if isinstance(ipv4, list) else str(ipv4))
            set_row(self.iface_table, r, 4, ", ".join(ipv6) if isinstance(ipv6, list) else str(ipv6))
            set_row(self.iface_table, r, 5, str(get_value(it, "speed", "")))

        self.route_table.setRowCount(len(routes))
        for r, route in enumerate(routes):
            set_row(self.route_table, r, 0, str(get_value(route, "destination", "")))
            set_row(self.route_table, r, 1, str(get_value(route, "gateway", "")))
            set_row(self.route_table, r, 2, str(get_value(route, "interface", "")))
            set_row(self.route_table, r, 3, str(get_value(route, "metric", "")))

        self.socket_table.setRowCount(len(sockets))
        for r, sock in enumerate(sockets):
            local = f"{get_value(sock, 'local_address', '')}:{get_value(sock, 'local_port', '')}"
            remote = f"{get_value(sock, 'remote_address', '')}:{get_value(sock, 'remote_port', '')}"
            set_row(self.socket_table, r, 0, str(get_value(sock, "proto", "")))
            set_row(self.socket_table, r, 1, local)
            set_row(self.socket_table, r, 2, remote)
            set_row(self.socket_table, r, 3, str(get_value(sock, "state", "")))
            set_row(self.socket_table, r, 4, str(get_value(sock, "pid", "")))
            set_row(self.socket_table, r, 5, str(get_value(sock, "process", "")))

        self.neighbor_table.setRowCount(len(neighbors))
        for r, neighbor in enumerate(neighbors):
            set_row(self.neighbor_table, r, 0, str(get_value(neighbor, "ip", "")))
            set_row(self.neighbor_table, r, 1, str(get_value(neighbor, "mac", "")))
            set_row(self.neighbor_table, r, 2, str(get_value(neighbor, "state", "")))
            set_row(self.neighbor_table, r, 3, str(get_value(neighbor, "interface", "")))

        self.ap_table.setRowCount(len(aps))
        for r, ap in enumerate(aps):
            set_row(self.ap_table, r, 0, str(get_value(ap, "ssid", "")))
            set_row(self.ap_table, r, 1, str(get_value(ap, "bssid", "")))
            set_row(self.ap_table, r, 2, str(get_value(ap, "channel", "")))
            set_row(self.ap_table, r, 3, str(get_value(ap, "signal", "")))
            set_row(self.ap_table, r, 4, str(get_value(ap, "security", "")))

        self.host_table.setRowCount(len(hosts))
        for r, h in enumerate(hosts):
            set_row(self.host_table, r, 0, str(get_value(h, "ip", "")))
            set_row(self.host_table, r, 1, str(get_value(h, "mac", "")))
            set_row(self.host_table, r, 2, str(get_value(h, "state", "")))
            set_row(self.host_table, r, 3, str(get_value(h, "source", "")))

        if self.holo_view is not None:
            try:
                iface_payload = [
                    {
                        "name": get_value(it, "name", ""),
                        "state": get_value(it, "state", ""),
                        "mac": get_value(it, "mac", ""),
                        "ipv4": get_value(it, "ipv4", []),
                        "ipv6": get_value(it, "ipv6", []),
                    }
                    for it in interfaces
                ]
                ap_payload = [
                    {
                        "ssid": get_value(ap, "ssid", ""),
                        "bssid": get_value(ap, "bssid", ""),
                        "chan": get_value(ap, "channel", ""),
                        "signal": get_value(ap, "signal", ""),
                        "security": get_value(ap, "security", ""),
                    }
                    for ap in aps
                ]
                host_payload = [
                    {
                        "ip": get_value(h, "ip", ""),
                        "mac": get_value(h, "mac", ""),
                        "state": get_value(h, "state", ""),
                    }
                    for h in hosts
                ]
                js = "window.netNinjaUpdate(%s);" % json.dumps(
                    {"interfaces": iface_payload, "aps": ap_payload, "hosts": host_payload},
                    ensure_ascii=False,
                )
                self.holo_view.page().runJavaScript(js)
            except Exception as exc:
                if self.main_window:
                    self.main_window._append_log_line(f"[discovery] Map update failed: {exc}")

        if errors and self.main_window:
            for err in errors:
                self.main_window._append_log_line(f"[discovery] {err}")


    def build_genome_group(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Sequencing Protocol"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.scan_presets.keys()))
        layout.addWidget(self.preset_combo)
        initiate_btn = create_glowing_button("Initiate Sequencing", self.run_selected_preset)
        self.main_window.apply_feature_support(initiate_btn, "discovery.nmap_standard")
        layout.addWidget(initiate_btn)
        layout.addStretch()
        return container

    def build_sequencing_group(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(12)

        grid.addWidget(QLabel("Initiate genome sequencing across common vectors."), 0, 0, 1, 2)
        quick_button = create_glowing_button("Rapid Sequencing (nmap -T4 -F)", self.run_quick)
        self.main_window.apply_feature_support(quick_button, "discovery.nmap_standard")
        grid.addWidget(quick_button, 1, 0)

        full_button = create_glowing_button("Full Genome Scan (-sS -sV -A -p-)", self.run_full)
        self.main_window.apply_feature_support(full_button, "discovery.nmap_full")
        grid.addWidget(full_button, 1, 1)

        stealth_button = create_glowing_button("Stealth Vector (-sS -T2 -f)", self.run_stealth)
        self.main_window.apply_feature_support(stealth_button, "discovery.nmap_full")
        grid.addWidget(stealth_button, 2, 0)

        udp_button = create_glowing_button("UDP Vector Scan (--top-ports 100)", self.run_udp)
        self.main_window.apply_feature_support(udp_button, "discovery.nmap_full")
        grid.addWidget(udp_button, 2, 1)

        vuln_button = create_glowing_button("Vulnerability Assay (--script vuln)", self.run_vuln)
        self.main_window.apply_feature_support(vuln_button, "discovery.nmap_standard")
        grid.addWidget(vuln_button, 3, 0)

        service_button = create_glowing_button("Service Fingerprinting (-sV)", self.run_service)
        self.main_window.apply_feature_support(service_button, "discovery.nmap_standard")
        grid.addWidget(service_button, 3, 1)

        return container

    def build_mass_group(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        layout.addWidget(QLabel("Specialized scans"), 0, 0, 1, 2)

        masscan_btn = create_glowing_button("Masscan (fast ports)", self.run_masscan)
        self.main_window.guard_button(masscan_btn, required_tools=["masscan"], require_admin=True)
        layout.addWidget(masscan_btn, 1, 0)

        rustscan_btn = create_glowing_button("Rustscan + nmap", self.run_rustscan)
        self.main_window.guard_button(rustscan_btn, required_tools=["rustscan"])
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
        self.executor(cmd, "Quick scan", target=target, feature_key="discovery.nmap_standard")

    def run_full(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -sV -sC -A -p- {quote(target)}"
        self.executor(cmd, "Full scan", target=target, feature_key="discovery.nmap_full")

    def run_stealth(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -T2 -f {quote(target)}"
        self.executor(cmd, "Stealth scan", target=target, feature_key="discovery.nmap_full")

    def run_udp(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sU --top-ports 100 {quote(target)}"
        self.executor(cmd, "UDP scan", target=target, feature_key="discovery.nmap_full")

    def run_vuln(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap --script vuln {quote(target)}"
        self.executor(cmd, "Vuln scan", target=target, feature_key="discovery.nmap_standard")

    def run_service(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap -sV {quote(target)}"
        self.executor(cmd, "Service scan", target=target, feature_key="discovery.nmap_standard")

    def run_masscan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        if not self.require_authorization("Masscan sweep"):
            if self.main_window:
                self.main_window._append_log_line("[info] Masscan cancelled (authorization phrase not provided)")
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
        self.target_field.scan_requested.connect(lambda field: self.main_window.scan_targets_for_field(field))
        self.main_window.guard_button(self.target_field.scan_btn, feature_flag="can_list_interfaces")
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
        self.discovery_feature_keys = {
            "Ping sweep (nmap -sn)": "recon.nmap_ping",
            "Netdiscover": "recon.netdiscover",
            "ARP scan (arp-scan -l)": "recon.arp_scan",
        }
        self.enum_feature_keys = {
            "DNS enum (dnsenum)": "recon.dnsenum",
            "DNS recon (dnsrecon)": "recon.dnsrecon",
            "SSL scan (sslscan)": "recon.sslscan",
            "SSLyze (sslyze)": "recon.sslyze",
            "SNMP sweep (onesixtyone)": "recon.onesixtyone",
            "SMB enum (enum4linux)": "recon.enum4linux",
        }
        self.add_panel("Target Scope", target_wrap, "Define the subnet/host to interrogate.", column_span=2)
        self.add_panel("Network Discovery", self.create_discovery_group())
        self.add_panel("Enumeration", self.create_enum_group())

    def create_discovery_group(self) -> QGroupBox:
        group = self.add_group("Network Discovery", "ARP, ping, and discovery scans.")
        btn_layout = QGridLayout()
        btn_layout.setSpacing(6)

        for idx, (label, template, desc) in enumerate(self.discovery_options):
            feature_key = self.discovery_feature_keys.get(label)
            button = create_glowing_button(
                label,
                lambda template=template, desc=desc, fk=feature_key: self.run_discovery(template, desc, fk),
            )
            if feature_key:
                self.main_window.apply_feature_support(button, feature_key)
            else:
                required = self.main_window._infer_required_tools(template)
                self.main_window.guard_button(
                    button,
                    required_tools=required,
                    require_admin=template.strip().startswith("sudo"),
                )
            btn_layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(btn_layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Quick discovery selection"))
        self.discovery_combo = QComboBox()
        self.discovery_combo.addItems([label for label, *_ in self.discovery_options])
        drop_layout.addWidget(self.discovery_combo)
        self.discovery_exec_button = create_glowing_button("Execute", self.run_discovery_dropdown)
        drop_layout.addWidget(self.discovery_exec_button)
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        self.discovery_combo.currentIndexChanged.connect(self._update_discovery_exec_state)
        self._update_discovery_exec_state()
        return group

    def create_enum_group(self) -> QGroupBox:
        group = self.add_group("Enumeration", "DNS, SSL/TLS, SNMP, and SMB mapping.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.enum_options):
            feature_key = self.enum_feature_keys.get(label)
            button = create_glowing_button(
                label,
                lambda template=template, desc=desc, fk=feature_key: self.run_enum(template, desc, fk),
            )
            if feature_key:
                self.main_window.apply_feature_support(button, feature_key)
            else:
                required = self.main_window._infer_required_tools(template)
                self.main_window.guard_button(
                    button,
                    required_tools=required,
                    require_admin=template.strip().startswith("sudo"),
                )
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Enumeration quick-run"))
        self.enum_combo = QComboBox()
        self.enum_combo.addItems([label for label, *_ in self.enum_options])
        drop_layout.addWidget(self.enum_combo)
        self.enum_exec_button = create_glowing_button("Run", self.run_enum_dropdown)
        drop_layout.addWidget(self.enum_exec_button)
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        self.enum_combo.currentIndexChanged.connect(self._update_enum_exec_state)
        self._update_enum_exec_state()
        return group

    def run_discovery(self, template: str, description: str, feature_key: Optional[str] = None) -> None:
        target = self.target_field.value()
        if "target" in template and not target:
            QMessageBox.warning(self, "Target missing", "Provide an IP/host/CIDR.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target or "broadcast", feature_key=feature_key)

    def run_enum(self, template: str, description: str, feature_key: Optional[str] = None) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a DNS name or host.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target, feature_key=feature_key)

    def run_discovery_dropdown(self) -> None:
        idx = self.discovery_combo.currentIndex()
        if idx < 0:
            return
        label, template, desc = self.discovery_options[idx]
        feature_key = self.discovery_feature_keys.get(label)
        self.run_discovery(template, desc, feature_key)

    def run_enum_dropdown(self) -> None:
        idx = self.enum_combo.currentIndex()
        if idx < 0:
            return
        label, template, desc = self.enum_options[idx]
        feature_key = self.enum_feature_keys.get(label)
        self.run_enum(template, desc, feature_key)

    def _update_discovery_exec_state(self) -> None:
        idx = self.discovery_combo.currentIndex()
        if idx < 0:
            self.discovery_exec_button.setEnabled(False)
            return
        _, template, _ = self.discovery_options[idx]
        label, _, _ = self.discovery_options[idx]
        feature_key = self.discovery_feature_keys.get(label)
        if feature_key:
            status = self.main_window.feature_status(feature_key)
            allowed = bool(status.get("enabled", True))
            reason = status.get("reason", "")
            recommended = status.get("recommended_path", "")
            base_support = status.get("base_support", "")
            badge = status.get("badge", "")
            self.main_window._register_feature_control(feature_key, self.discovery_exec_button)
            self.main_window._apply_support_badge(self.discovery_exec_button, badge)
            tip_parts = []
            if reason:
                tip_parts.append(str(reason))
            if recommended:
                tip_parts.append(f"Recommended path: {recommended}")
            tooltip = " ".join(tip_parts).strip()
            if tooltip:
                self.discovery_exec_button.setToolTip(tooltip)
            if base_support in ("unsupported", "external_required"):
                allowed = False
            self.discovery_exec_button.setEnabled(allowed)
            return
        required = self.main_window._infer_required_tools(template)
        require_admin = template.strip().startswith("sudo")
        allowed = True
        reason = ""
        for tool in required:
            if not (self.main_window.capabilities.tools.get(tool, False) or shutil.which(tool)):
                if self.main_window.capabilities.is_windows and self.main_window.capabilities.tools.get("wsl", False):
                    reason = f"Requires WSL tool: {tool}"
                    continue
                allowed = False
                reason = f"Missing tool: {tool}"
                break
        if require_admin and not self.main_window.capabilities.is_admin:
            allowed = False
            reason = "Requires administrator/root privileges"
        self.discovery_exec_button.setEnabled(allowed)
        if reason:
            self.discovery_exec_button.setToolTip(reason)

    def _update_enum_exec_state(self) -> None:
        idx = self.enum_combo.currentIndex()
        if idx < 0:
            self.enum_exec_button.setEnabled(False)
            return
        _, template, _ = self.enum_options[idx]
        label, _, _ = self.enum_options[idx]
        feature_key = self.enum_feature_keys.get(label)
        if feature_key:
            status = self.main_window.feature_status(feature_key)
            allowed = bool(status.get("enabled", True))
            reason = status.get("reason", "")
            recommended = status.get("recommended_path", "")
            base_support = status.get("base_support", "")
            badge = status.get("badge", "")
            self.main_window._register_feature_control(feature_key, self.enum_exec_button)
            self.main_window._apply_support_badge(self.enum_exec_button, badge)
            tip_parts = []
            if reason:
                tip_parts.append(str(reason))
            if recommended:
                tip_parts.append(f"Recommended path: {recommended}")
            tooltip = " ".join(tip_parts).strip()
            if tooltip:
                self.enum_exec_button.setToolTip(tooltip)
            if base_support in ("unsupported", "external_required"):
                allowed = False
            self.enum_exec_button.setEnabled(allowed)
            return
        required = self.main_window._infer_required_tools(template)
        require_admin = template.strip().startswith("sudo")
        allowed = True
        reason = ""
        for tool in required:
            if not (self.main_window.capabilities.tools.get(tool, False) or shutil.which(tool)):
                if self.main_window.capabilities.is_windows and self.main_window.capabilities.tools.get("wsl", False):
                    reason = f"Requires WSL tool: {tool}"
                    continue
                allowed = False
                reason = f"Missing tool: {tool}"
                break
        if require_admin and not self.main_window.capabilities.is_admin:
            allowed = False
            reason = "Requires administrator/root privileges"
        self.enum_exec_button.setEnabled(allowed)
        if reason:
            self.enum_exec_button.setToolTip(reason)


class WirelessTab(CategoryTab):
    """WIRELESS tab for interface control, reconnaissance, and cracking."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.executor = executor
        self.iface_field = TargetField("Wireless interface", share_history=False)
        self.iface_field.scan_btn.setText("Refresh Interfaces")
        self.iface_field.scan_requested.connect(lambda _field: self.refresh_interfaces())
        self.main_window.guard_button(self.iface_field.scan_btn, feature_flag="can_list_interfaces")
        main_window.register_target_field(self.iface_field)
        self.bssid_field = TargetField("Target BSSID", share_history=True)
        self.bssid_field.scan_btn.setText("Scan Wi-Fi")
        self.bssid_field.scan_requested.connect(lambda _field: self.refresh_bssids())
        self.main_window.guard_button(self.bssid_field.scan_btn, feature_flag="can_scan_wifi")
        # Register BSSID field with the main window for shared history
        if main_window:
            main_window.register_bssid_field(self.bssid_field)
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel")
        self.attack_combo = QComboBox()
        self.attack_combo.addItems(
            ["Deauth attack", "WPS attack (reaver)", "Handshake capture"]
        )
        self.attack_feature_keys = {
            "Deauth attack": "wireless.packet_injection",
            "WPS attack (reaver)": "wireless.wps_attack",
            "Handshake capture": "wireless.handshake_capture",
        }
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
        self.main_window.apply_feature_support(enable_btn, "wireless.monitor_mode")
        self.main_window.apply_feature_support(disable_btn, "wireless.monitor_mode")
        self.main_window.guard_button(refresh_btn, feature_flag="can_list_interfaces")
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
        self.main_window.apply_feature_support(airodump, "wireless.airodump")
        self.main_window.apply_feature_support(bettercap, "wireless.bettercap")
        self.main_window.apply_feature_support(wifite, "wireless.wifite")
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
        self.main_window.apply_feature_support(deauth_btn, "wireless.packet_injection")
        self.main_window.apply_feature_support(wps_btn, "wireless.wps_attack")
        self.main_window.apply_feature_support(handshake_btn, "wireless.handshake_capture")
        layout.addWidget(deauth_btn, 0, 0)
        layout.addWidget(wps_btn, 0, 1)
        layout.addWidget(handshake_btn, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Attack preset"))
        drop_layout.addWidget(self.attack_combo)
        self.attack_exec_button = create_glowing_button("Launch attack", self.run_selected_wireless_attack)
        drop_layout.addWidget(self.attack_exec_button)
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        self.attack_combo.currentIndexChanged.connect(self._update_attack_exec_state)
        self._update_attack_exec_state()
        return group

    def build_cracking_group(self) -> QGroupBox:
        group = self.add_group("Cracking & conversion", "Aircrack-ng / Hashcat helpers.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        aircrack_btn = create_glowing_button("Crack with aircrack-ng", self.run_aircrack)
        hashcat_btn = create_glowing_button("Crack with hashcat", self.run_hashcat)
        convert_btn = create_glowing_button("Convert .cap -> .hc22000", self.convert_handshake)
        self.main_window.apply_feature_support(aircrack_btn, "wireless.aircrack")
        self.main_window.apply_feature_support(hashcat_btn, "wireless.hashcat")
        self.main_window.apply_feature_support(convert_btn, "wireless.convert_handshake")
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
        """Populate the interface selector using the provider."""
        def precheck() -> tuple[bool, str, str]:
            if not self.main_window.capabilities.flag("can_list_interfaces"):
                reason = self.main_window.capabilities.reason("can_list_interfaces") or "Interface discovery unavailable"
                return False, reason, "Install required tools or run with elevated privileges."
            return True, "", ""

        def execute() -> ExecutionResult:
            start = time.time()
            interfaces = self.main_window.provider.get_interfaces()
            return ExecutionResult(returncode=0, payload={"interfaces": interfaces}, elapsed=time.time() - start)

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            interfaces = result.payload.get("interfaces", [])
            names = [getattr(it, "name", "") if not isinstance(it, dict) else it.get("name", "") for it in interfaces]
            summary = {"interfaces": len([n for n in names if n])}
            return {"summary": summary, "items": [], "names": [n for n in names if n]}

        def ui_update(payload: Dict[str, Any]) -> None:
            names = payload.get("names", [])
            self.iface_field.combo.clear()
            if names:
                self.iface_field.combo.addItems(names)
            summary = ", ".join(names) if names else "no interfaces detected"
            self.main_window._append_log_line(f"[wireless] Interfaces refreshed: {summary}")

        job = JobSpec(
            name="Refresh Interfaces",
            category="wireless",
            precheck=precheck,
            execute=execute,
            parse=parse,
            ui_update=ui_update,
        )
        self.run_job(job)

    def refresh_bssids(self) -> None:
        """Populate the BSSID selector from a Wi-Fi scan."""
        def precheck() -> tuple[bool, str, str]:
            if not self.main_window.capabilities.flag("can_scan_wifi"):
                reason = self.main_window.capabilities.reason("can_scan_wifi") or "Wi-Fi scan unavailable"
                return False, reason, "Install required tools or run with elevated privileges."
            return True, "", ""

        def execute() -> ExecutionResult:
            start = time.time()
            aps = self.main_window.provider.scan_wifi()
            return ExecutionResult(returncode=0, payload={"aps": aps}, elapsed=time.time() - start)

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            aps = result.payload.get("aps", [])
            bssids = [getattr(ap, "bssid", "") if not isinstance(ap, dict) else ap.get("bssid", "") for ap in aps]
            summary = {"bssids": len([b for b in bssids if b])}
            return {"summary": summary, "items": [], "bssids": [b for b in bssids if b]}

        def ui_update(payload: Dict[str, Any]) -> None:
            bssids = payload.get("bssids", [])
            self.bssid_field.combo.clear()
            if bssids:
                self.bssid_field.combo.addItems(bssids)
            summary = ", ".join(bssids) if bssids else "no BSSIDs detected"
            self.main_window._append_log_line(f"[wireless] BSSIDs refreshed: {summary}")

        job = JobSpec(
            name="Scan Wi-Fi",
            category="wireless",
            precheck=precheck,
            execute=execute,
            parse=parse,
            ui_update=ui_update,
        )
        self.run_job(job)

    def enable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng start {quote(iface)}"
        self.executor(cmd, "Enable monitor mode", target=iface, feature_key="wireless.monitor_mode")

    def disable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng stop {quote(iface)}"
        self.executor(cmd, "Disable monitor", target=iface, feature_key="wireless.monitor_mode")

    def run_airodump(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo timeout 15 airodump-ng {quote(iface)}"
        self.executor(cmd, "airodump-ng scan", target=iface, feature_key="wireless.airodump")

    def run_bettercap(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo bettercap -iface {quote(iface)} -eval 'set arp.spoof.fullduplex true; net.sniff on'"
        self.executor(cmd, "Bettercap session", target=iface, feature_key="wireless.bettercap")

    def run_wifite(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo wifite -i {quote(iface)} --kill"
        self.executor(cmd, "Wifite attack", target=iface, feature_key="wireless.wifite")

    def deauth_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or "FF:FF:FF:FF:FF:FF"
        if not self.require_authorization("Deauth attack"):
            if self.main_window:
                self.main_window._append_log_line("[info] Deauth attack cancelled (authorization phrase not provided)")
            return
        if self.main_window and self.bssid_field.value():
            self.main_window.add_bssid_history(self.bssid_field.value())
        cmd = f"sudo aireplay-ng --deauth 10 -a {quote(target)} {quote(iface)}"
        self.executor(cmd, "Deauth", target=iface, feature_key="wireless.packet_injection")

    def wps_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or ""
        if not target:
            QMessageBox.warning(self, "BSSID required", "Provide a target BSSID for WPS attacks.")
            return
        if not self.require_authorization("WPS attack"):
            if self.main_window:
                self.main_window._append_log_line("[info] WPS attack cancelled (authorization phrase not provided)")
            return
        if self.main_window:
            self.main_window.add_bssid_history(target)
        channel = self.channel_input.text().strip()
        channel_arg = f"-c {quote(channel)}" if channel else ""
        cmd = f"sudo reaver -i {quote(iface)} -b {quote(target)} {channel_arg} -N -vv"
        self.executor(cmd, "WPS attack (reaver)", target=target, feature_key="wireless.wps_attack")

    def capture_handshake(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value()
        if not target:
            QMessageBox.warning(self, "BSSID missing", "Provide the target BSSID for capture.")
            return
        if not self.require_authorization("Handshake capture"):
            if self.main_window:
                self.main_window._append_log_line("[info] Handshake capture cancelled (authorization phrase not provided)")
            return
        if self.main_window:
            self.main_window.add_bssid_history(target)
        channel = self.channel_input.text().strip()
        channel_arg = f"-c {quote(channel)}" if channel else ""
        cmd = f"sudo timeout 20 airodump-ng --bssid {quote(target)} {channel_arg} -w /tmp/handshake {quote(iface)}"
        self.executor(cmd, "Handshake capture", target=target, feature_key="wireless.handshake_capture")

    def run_aircrack(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/capture.cap")
        if not ok or not capfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"aircrack-ng -w {quote(wordlist)} {quote(capfile)}"
        self.executor(cmd, "Aircrack-ng", target=capfile, feature_key="wireless.aircrack")

    def run_hashcat(self) -> None:
        hashfile, ok = self.request_input("Hash/Capture file", "/tmp/hash.hc22000")
        if not ok or not hashfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"hashcat -m 22000 -a 0 {quote(hashfile)} {quote(wordlist)} --status --potfile-path /tmp/hashcat.pot"
        self.executor(cmd, "Hashcat", target=hashfile, feature_key="wireless.hashcat")

    def convert_handshake(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/handshake.cap")
        if not ok or not capfile:
            return
        cmd = f"hcxpcapngtool -o {quote(capfile)}.hc22000 {quote(capfile)}"
        self.executor(cmd, "Convert handshake", target=capfile, feature_key="wireless.convert_handshake")

    def run_selected_wireless_attack(self) -> None:
        choice = self.attack_combo.currentText()
        if choice == "Deauth attack":
            self.deauth_attack()
        elif choice == "WPS attack (reaver)":
            self.wps_attack()
        elif choice == "Handshake capture":
            self.capture_handshake()

    def _update_attack_exec_state(self) -> None:
        choice = self.attack_combo.currentText()
        feature_key = self.attack_feature_keys.get(choice)
        if feature_key:
            status = self.main_window.feature_status(feature_key)
            allowed = bool(status.get("enabled", True))
            reason = status.get("reason", "")
            recommended = status.get("recommended_path", "")
            base_support = status.get("base_support", "")
            badge = status.get("badge", "")
            self.main_window._register_feature_control(feature_key, self.attack_exec_button)
            self.main_window._apply_support_badge(self.attack_exec_button, badge)
            tip_parts = []
            if reason:
                tip_parts.append(str(reason))
            if recommended:
                tip_parts.append(f"Recommended path: {recommended}")
            tooltip = " ".join(tip_parts).strip()
            if tooltip:
                self.attack_exec_button.setToolTip(tooltip)
            if base_support in ("unsupported", "external_required"):
                allowed = False
            self.attack_exec_button.setEnabled(allowed)
            return
        self.attack_exec_button.setEnabled(True)

    def request_input(self, prompt: str, default: str = "") -> Tuple[str, bool]:
        value, ok = QInputDialog.getText(self, "Input required", prompt, text=default)
        return value, ok


class WebTab(CategoryTab):
    """WEB tab for scanners and injection tools."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.target_field = TargetField("URL / Domain")
        self.target_field.scan_requested.connect(lambda field: self.main_window.scan_targets_for_field(field))
        self.main_window.guard_button(self.target_field.scan_btn, feature_flag="can_list_interfaces")
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
        self.web_feature_keys = {
            "SQLmap": "web.sqlmap",
            "Nikto": "web.nikto",
            "Nuclei": "web.nuclei",
            "XSStrike": "web.xsstrike",
            "Commix": "web.commix",
        }
        self.dir_feature_keys = {
            "Gobuster": "web.gobuster",
            "Dirb": "web.dirb",
            "Feroxbuster": "web.feroxbuster",
        }
        self.add_panel("Target URL / Domain", target_wrap, "Scope for scanners and brute-force", column_span=2)
        self.add_panel("Scanners & Injection", self.build_web_tools_group())
        self.add_panel("Directory Brute-force", self.build_directory_group())

    def build_web_tools_group(self) -> QGroupBox:
        group = self.add_group("Scanners & injection", "SQLmap, Nikto, nuclei, Commix, XSStrike.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.web_scanners):
            feature_key = self.web_feature_keys.get(label)
            button = create_glowing_button(
                label,
                lambda t=template, d=desc, fk=feature_key: self.run_web_tool(t, d, fk),
            )
            if feature_key:
                self.main_window.apply_feature_support(button, feature_key)
            else:
                required = self.main_window._infer_required_tools(template)
                self.main_window.guard_button(button, required_tools=required)
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Select scanner"))
        self.web_combo = QComboBox()
        self.web_combo.addItems([label for label, *_ in self.web_scanners])
        drop_layout.addWidget(self.web_combo)
        self.web_exec_button = create_glowing_button("Launch", self.run_web_combo)
        drop_layout.addWidget(self.web_exec_button)
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        self.web_combo.currentIndexChanged.connect(self._update_web_exec_state)
        self._update_web_exec_state()
        return group

    def build_directory_group(self) -> QGroupBox:
        group = self.add_group("Directory brute-force", "Gobuster, Dirb, Feroxbuster.")
        layout = QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        for idx, (label, template) in enumerate(self.dir_tools):
            feature_key = self.dir_feature_keys.get(label)
            button = create_glowing_button(
                label,
                lambda t=template, fk=feature_key: self.run_dir_tool(t, fk),
            )
            if feature_key:
                self.main_window.apply_feature_support(button, feature_key)
            else:
                required = self.main_window._infer_required_tools(template)
                self.main_window.guard_button(button, required_tools=required)
            layout.addWidget(button, idx // 2, idx % 2)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Directory fuzz"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItems([label for label, *_ in self.dir_tools])
        drop_layout.addWidget(self.dir_combo)
        self.dir_exec_button = create_glowing_button("Start", self.run_dir_combo)
        drop_layout.addWidget(self.dir_exec_button)
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        self.dir_combo.currentIndexChanged.connect(self._update_dir_exec_state)
        self._update_dir_exec_state()
        return group

    def run_web_tool(self, template: str, description: str, feature_key: Optional[str] = None) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a URL before running.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target, feature_key=feature_key)

    def run_dir_tool(self, template: str, feature_key: Optional[str] = None) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a target URL.")
            return
        command = template.format(target=quote(target))
        self.executor(command, "Directory bruteforce", target=target, feature_key=feature_key)

    def run_web_combo(self) -> None:
        idx = self.web_combo.currentIndex()
        if idx < 0:
            return
        label, template, desc = self.web_scanners[idx]
        feature_key = self.web_feature_keys.get(label)
        self.run_web_tool(template, desc, feature_key)

    def run_dir_combo(self) -> None:
        idx = self.dir_combo.currentIndex()
        if idx < 0:
            return
        label, template = self.dir_tools[idx]
        feature_key = self.dir_feature_keys.get(label)
        self.run_dir_tool(template, feature_key)

    def _update_web_exec_state(self) -> None:
        idx = self.web_combo.currentIndex()
        if idx < 0:
            self.web_exec_button.setEnabled(False)
            return
        label, template, _ = self.web_scanners[idx]
        feature_key = self.web_feature_keys.get(label)
        if feature_key:
            status = self.main_window.feature_status(feature_key)
            allowed = bool(status.get("enabled", True))
            reason = status.get("reason", "")
            recommended = status.get("recommended_path", "")
            base_support = status.get("base_support", "")
            badge = status.get("badge", "")
            self.main_window._register_feature_control(feature_key, self.web_exec_button)
            self.main_window._apply_support_badge(self.web_exec_button, badge)
            tip_parts = []
            if reason:
                tip_parts.append(str(reason))
            if recommended:
                tip_parts.append(f"Recommended path: {recommended}")
            tooltip = " ".join(tip_parts).strip()
            if tooltip:
                self.web_exec_button.setToolTip(tooltip)
            if base_support in ("unsupported", "external_required"):
                allowed = False
            self.web_exec_button.setEnabled(allowed)
            return
        required = self.main_window._infer_required_tools(template)
        allowed = True
        reason = ""
        for tool in required:
            if not (self.main_window.capabilities.tools.get(tool, False) or shutil.which(tool)):
                if self.main_window.capabilities.is_windows and self.main_window.capabilities.tools.get("wsl", False):
                    reason = f"Requires WSL tool: {tool}"
                    continue
                allowed = False
                reason = f"Missing tool: {tool}"
                break
        self.web_exec_button.setEnabled(allowed)
        if reason:
            self.web_exec_button.setToolTip(reason)

    def _update_dir_exec_state(self) -> None:
        idx = self.dir_combo.currentIndex()
        if idx < 0:
            self.dir_exec_button.setEnabled(False)
            return
        label, template = self.dir_tools[idx]
        feature_key = self.dir_feature_keys.get(label)
        if feature_key:
            status = self.main_window.feature_status(feature_key)
            allowed = bool(status.get("enabled", True))
            reason = status.get("reason", "")
            recommended = status.get("recommended_path", "")
            base_support = status.get("base_support", "")
            badge = status.get("badge", "")
            self.main_window._register_feature_control(feature_key, self.dir_exec_button)
            self.main_window._apply_support_badge(self.dir_exec_button, badge)
            tip_parts = []
            if reason:
                tip_parts.append(str(reason))
            if recommended:
                tip_parts.append(f"Recommended path: {recommended}")
            tooltip = " ".join(tip_parts).strip()
            if tooltip:
                self.dir_exec_button.setToolTip(tooltip)
            if base_support in ("unsupported", "external_required"):
                allowed = False
            self.dir_exec_button.setEnabled(allowed)
            return
        required = self.main_window._infer_required_tools(template)
        allowed = True
        reason = ""
        for tool in required:
            if not (self.main_window.capabilities.tools.get(tool, False) or shutil.which(tool)):
                if self.main_window.capabilities.is_windows and self.main_window.capabilities.tools.get("wsl", False):
                    reason = f"Requires WSL tool: {tool}"
                    continue
                allowed = False
                reason = f"Missing tool: {tool}"
                break
        self.dir_exec_button.setEnabled(allowed)
        if reason:
            self.dir_exec_button.setToolTip(reason)




class WSDiscoveryWorker(QThread):
    """
    Background worker that performs ONVIF WS-Discovery so the UI stays responsive.
    """
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, timeout_s: float = 1.5, retries: int = 2, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._timeout_s = timeout_s
        self._retries = retries

    def run(self) -> None:
        try:
            cams = ws_discover(timeout_s=self._timeout_s, retries=self._retries)
            self.results_ready.emit([c.as_dict() for c in cams])
        except Exception as exc:
            self.error.emit(f"Discovery failed: {exc!r}")


class IPCameraTab(QWidget):
    """
    Feature-rich IP camera tab:
    - Supports generic RTSP / HTTP(S) streams via Qt Multimedia (QMediaPlayer).
    - ONVIF WS-Discovery for device discovery (best-effort).
    - Snapshot capture.
    - Motion + tamper detection using frame differencing from QVideoSink.
    - AlfredCamera compatibility via embedded WebViewer (Qt WebEngine if available).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._player: Optional[QMediaPlayer] = None
        self._audio: Optional[QAudioOutput] = None
        self._video_widget: Optional[QVideoWidget] = None
        self._sink: Optional[QVideoSink] = None

        self._last_frame_gray = None  # type: ignore[assignment]
        self._last_motion_ts = 0.0
        self._motion_armed = False
        self._tamper_armed = False
        self._auto_reconnect = True
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

        self._settings = QSettings("NetNinja", "NetReaper")
        self._build_ui()
        self._load_profiles()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QLabel("IP Cameras — Live View, Discovery, Detection")
        header.setObjectName("sectionTitle")
        root.addWidget(header)

        top = QHBoxLayout()
        root.addLayout(top, stretch=1)

        # Left control panel
        left = QVBoxLayout()
        left.setSpacing(10)
        top.addLayout(left, stretch=0)

        conn_box = QGroupBox("Connect")
        conn_layout = QGridLayout(conn_box)
        conn_layout.setHorizontalSpacing(8)
        conn_layout.setVerticalSpacing(8)

        self.profile_combo = QComboBox()
        self.profile_combo.setEditable(False)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)

        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("Profile name (e.g., Front Door)")

        self.stream_type = QComboBox()
        self.stream_type.addItems(["RTSP", "HTTP(S) (MJPEG/HLS)", "AlfredCamera WebViewer"])
        self.stream_type.currentIndexChanged.connect(self._on_stream_type_changed)

        self.host_field = QLineEdit()
        self.host_field.setPlaceholderText("IP or hostname (e.g., 192.168.1.120)")
        self.port_field = QLineEdit()
        self.port_field.setPlaceholderText("Port (e.g., 554)")
        self.port_field.setText("554")
        self.user_field = QLineEdit()
        self.user_field.setPlaceholderText("Username (optional)")
        self.pass_field = QLineEdit()
        self.pass_field.setPlaceholderText("Password (optional)")
        self.pass_field.setEchoMode(QLineEdit.EchoMode.Password)

        self.url_field = QLineEdit()
        self.url_field.setPlaceholderText("Full stream URL (if you already have it)")

        self.discover_btn = QPushButton("Discover (ONVIF)")
        self.discover_btn.clicked.connect(self._discover_onvif)

        self.guess_btn = QPushButton("Guess RTSP URLs")
        self.guess_btn.clicked.connect(self._guess_urls)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._connect)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._disconnect)

        self.save_profile_btn = QPushButton("Save / Update Profile")
        self.save_profile_btn.clicked.connect(self._save_profile)

        self.delete_profile_btn = QPushButton("Delete Profile")
        self.delete_profile_btn.clicked.connect(self._delete_profile)

        row = 0
        conn_layout.addWidget(QLabel("Saved profiles"), row, 0)
        conn_layout.addWidget(self.profile_combo, row, 1, 1, 2)
        row += 1

        conn_layout.addWidget(QLabel("Profile name"), row, 0)
        conn_layout.addWidget(self.profile_name, row, 1, 1, 2)
        row += 1

        conn_layout.addWidget(QLabel("Mode"), row, 0)
        conn_layout.addWidget(self.stream_type, row, 1, 1, 2)
        row += 1

        conn_layout.addWidget(QLabel("Host"), row, 0)
        conn_layout.addWidget(self.host_field, row, 1)
        conn_layout.addWidget(self.discover_btn, row, 2)
        row += 1

        conn_layout.addWidget(QLabel("Port"), row, 0)
        conn_layout.addWidget(self.port_field, row, 1)
        conn_layout.addWidget(self.guess_btn, row, 2)
        row += 1

        conn_layout.addWidget(QLabel("User"), row, 0)
        conn_layout.addWidget(self.user_field, row, 1, 1, 2)
        row += 1

        conn_layout.addWidget(QLabel("Pass"), row, 0)
        conn_layout.addWidget(self.pass_field, row, 1, 1, 2)
        row += 1

        conn_layout.addWidget(QLabel("URL"), row, 0)
        conn_layout.addWidget(self.url_field, row, 1, 1, 2)
        row += 1

        buttons = QHBoxLayout()
        buttons.addWidget(self.connect_btn)
        buttons.addWidget(self.disconnect_btn)
        left.addWidget(conn_box)
        left.addLayout(buttons)

        prof_btns = QHBoxLayout()
        prof_btns.addWidget(self.save_profile_btn)
        prof_btns.addWidget(self.delete_profile_btn)
        left.addLayout(prof_btns)

        detect_box = QGroupBox("Detection (Local)")
        dlay = QGridLayout(detect_box)
        dlay.setHorizontalSpacing(8)
        dlay.setVerticalSpacing(8)

        self.motion_toggle = QCheckBox("Motion detection")
        self.motion_toggle.stateChanged.connect(self._toggle_motion)

        self.tamper_toggle = QCheckBox("Tamper / blackout detection")
        self.tamper_toggle.stateChanged.connect(self._toggle_tamper)

        self.sensitivity = QComboBox()
        self.sensitivity.addItems(["Low", "Medium", "High"])
        self.sensitivity.setCurrentIndex(1)

        self.cooldown = QComboBox()
        self.cooldown.addItems(["0s", "1s", "3s", "5s", "10s"])
        self.cooldown.setCurrentIndex(2)

        self.snapshot_btn = QPushButton("Snapshot")
        self.snapshot_btn.clicked.connect(self._snapshot)

        self.auto_reconnect_cb = QCheckBox("Auto reconnect")
        self.auto_reconnect_cb.setChecked(True)
        self.auto_reconnect_cb.stateChanged.connect(self._toggle_reconnect)

        drow = 0
        dlay.addWidget(self.motion_toggle, drow, 0, 1, 2)
        drow += 1
        dlay.addWidget(self.tamper_toggle, drow, 0, 1, 2)
        drow += 1
        dlay.addWidget(QLabel("Sensitivity"), drow, 0)
        dlay.addWidget(self.sensitivity, drow, 1)
        drow += 1
        dlay.addWidget(QLabel("Cooldown"), drow, 0)
        dlay.addWidget(self.cooldown, drow, 1)
        drow += 1
        dlay.addWidget(self.auto_reconnect_cb, drow, 0, 1, 2)
        drow += 1
        dlay.addWidget(self.snapshot_btn, drow, 0, 1, 2)

        left.addWidget(detect_box)

        self.status = QLabel("Status: idle")
        self.status.setObjectName("mutedLabel")
        left.addWidget(self.status)

        self.event_log = QPlainTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMinimumWidth(360)
        self.event_log.setPlaceholderText("Detection + connection events will appear here.")
        left.addWidget(self.event_log, stretch=1)

        # Right view panel (video / embedded web)
        self.view_stack = QStackedWidget()
        top.addWidget(self.view_stack, stretch=1)

        # Video view
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self._video_widget = QVideoWidget()
        video_layout.addWidget(self._video_widget, stretch=1)
        self.view_stack.addWidget(video_container)

        # Alfred view (Qt WebEngine; fall back to external browser)
        self.alfred_container = QWidget()
        al = QVBoxLayout(self.alfred_container)
        al.setContentsMargins(0, 0, 0, 0)
        self.alfred_hint = QLabel(
            "AlfredCamera runs primarily through its own app and WebViewer.\n"
            "Use this mode to open Alfred's WebViewer inside NetReaper (when supported) or launch it in your browser.\n"
            "Tip: you must sign in with the same Alfred account as your camera device.\n"
        )
        self.alfred_hint.setWordWrap(True)
        al.addWidget(self.alfred_hint)

        self.open_alfred_btn = QPushButton("Open Alfred WebViewer")
        self.open_alfred_btn.clicked.connect(self._open_alfred)

        # Ensure camera action buttons are always readable and not "mystery blanks" under any platform theme.
        for _b in (
            self.discover_btn,
            self.guess_btn,
            self.connect_btn,
            self.disconnect_btn,
            self.save_profile_btn,
            self.delete_profile_btn,
            self.snapshot_btn,
            self.open_alfred_btn,
        ):
            _b.setMinimumHeight(36)
            _b.setCursor(Qt.CursorShape.PointingHandCursor)
            _b.setProperty("camAction", "true")

        al.addWidget(self.open_alfred_btn)

        self.alfred_web_placeholder = QLabel("WebViewer panel will appear here if Qt WebEngine is available.")
        self.alfred_web_placeholder.setWordWrap(True)
        al.addWidget(self.alfred_web_placeholder, stretch=1)
        self.view_stack.addWidget(self.alfred_container)

        self.view_stack.setCurrentIndex(0)
        self._on_stream_type_changed()

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.event_log.appendPlainText(f"[{ts}] {msg}")
        self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum())

    def _set_status(self, msg: str) -> None:
        self.status.setText(f"Status: {msg}")

    def _profiles_key(self) -> str:
        return "ip_camera/profiles_v1"

    def _load_profiles(self) -> None:
        raw = self._settings.value(self._profiles_key(), defaultValue="[]")
        try:
            profs = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            profs = []
        if not isinstance(profs, list):
            profs = []
        self._profiles = profs  # type: ignore[assignment]

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("(select)", userData=None)
        for p in self._profiles:
            name = str(p.get("name", "Unnamed"))
            self.profile_combo.addItem(name, userData=p)
        self.profile_combo.blockSignals(False)

    def _save_profiles(self) -> None:
        self._settings.setValue(self._profiles_key(), json.dumps(self._profiles))

    def _on_profile_selected(self) -> None:
        p = self.profile_combo.currentData()
        if not isinstance(p, dict):
            return
        self.profile_name.setText(str(p.get("name", "")))
        self.stream_type.setCurrentText(str(p.get("mode", "RTSP")))
        self.host_field.setText(str(p.get("host", "")))
        self.port_field.setText(str(p.get("port", "554")))
        self.user_field.setText(str(p.get("username", "")))
        self.pass_field.setText(str(p.get("password", "")))
        self.url_field.setText(str(p.get("url", "")))
        self._on_stream_type_changed()

    def _save_profile(self) -> None:
        name = self.profile_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please provide a profile name.")
            return

        p = {
            "name": name,
            "mode": self.stream_type.currentText(),
            "host": self.host_field.text().strip(),
            "port": self.port_field.text().strip(),
            "username": self.user_field.text(),
            "password": self.pass_field.text(),
            "url": self.url_field.text().strip(),
        }

        replaced = False
        for i, old in enumerate(self._profiles):
            if str(old.get("name", "")).strip().lower() == name.lower():
                self._profiles[i] = p
                replaced = True
                break
        if not replaced:
            self._profiles.append(p)

        self._save_profiles()
        self._load_profiles()
        self._log(f"Saved profile: {name}")

    def _delete_profile(self) -> None:
        p = self.profile_combo.currentData()
        if not isinstance(p, dict):
            QMessageBox.information(self, "Delete Profile", "Select a profile first.")
            return
        name = str(p.get("name", "")).strip()
        if not name:
            return
        self._profiles = [x for x in self._profiles if str(x.get("name", "")).strip().lower() != name.lower()]
        self._save_profiles()
        self._load_profiles()
        self._log(f"Deleted profile: {name}")

    def _toggle_motion(self) -> None:
        self._motion_armed = bool(self.motion_toggle.isChecked())
        self._log(f"Motion detection {'enabled' if self._motion_armed else 'disabled'}")

    def _toggle_tamper(self) -> None:
        self._tamper_armed = bool(self.tamper_toggle.isChecked())
        self._log(f"Tamper detection {'enabled' if self._tamper_armed else 'disabled'}")

    def _toggle_reconnect(self) -> None:
        self._auto_reconnect = bool(self.auto_reconnect_cb.isChecked())
        self._log(f"Auto reconnect {'enabled' if self._auto_reconnect else 'disabled'}")

    def _cooldown_seconds(self) -> float:
        txt = self.cooldown.currentText().replace("s", "").strip()
        try:
            return float(txt)
        except Exception:
            return 3.0

    def _motion_threshold(self) -> float:
        level = self.sensitivity.currentText()
        if level == "Low":
            return 0.10
        if level == "High":
            return 0.03
        return 0.06

    def _on_stream_type_changed(self) -> None:
        mode = self.stream_type.currentText()
        if mode == "AlfredCamera WebViewer":
            self.view_stack.setCurrentIndex(1)
            self._disconnect()
            self._set_status("Alfred mode ready")
        else:
            self.view_stack.setCurrentIndex(0)

    def _discover_onvif(self) -> None:
        self._set_status("discovering ONVIF devices…")
        self._log("Starting ONVIF WS-Discovery…")
        self.discover_btn.setEnabled(False)

        self._disc_worker = WSDiscoveryWorker(timeout_s=1.8, retries=3, parent=self)
        self._disc_worker.results_ready.connect(self._on_discovery_results)
        self._disc_worker.error.connect(self._on_discovery_error)
        self._disc_worker.finished.connect(lambda: self.discover_btn.setEnabled(True))
        self._disc_worker.start()

    def _on_discovery_error(self, msg: str) -> None:
        self._set_status("discovery failed")
        self._log(msg)
        QMessageBox.warning(self, "Discovery Failed", msg)

    def _on_discovery_results(self, cams: list) -> None:
        self._set_status(f"discovered {len(cams)} device(s)")
        if not cams:
            self._log("No ONVIF devices found.")
            QMessageBox.information(
                self,
                "Discovery",
                "No ONVIF devices were found via WS-Discovery.\n\n"
                "This is common if the camera disables ONVIF or is on a different VLAN/subnet.",
            )
            return

        menu = QMenu(self)
        for c in cams:
            ip = str(c.get("ip", ""))
            xaddrs = c.get("xaddrs", [])
            label = ip if ip else (xaddrs[0] if xaddrs else "Unknown device")
            act = menu.addAction(label)
            act.setData(c)

        chosen = menu.exec(self.discover_btn.mapToGlobal(self.discover_btn.rect().bottomLeft()))
        if not chosen:
            return
        data = chosen.data()
        if isinstance(data, dict):
            self.host_field.setText(str(data.get("ip", "")))
            self._log(f"Selected device: {data.get('ip','')}")
            xaddrs = data.get("xaddrs", [])
            if xaddrs and not self.url_field.text().strip():
                self.url_field.setText(str(xaddrs[0]))

    def _guess_urls(self) -> None:
        ip = self.host_field.text().strip()
        if not ip:
            QMessageBox.warning(self, "Missing Host", "Enter a camera IP/host first.")
            return

        try:
            port = int(self.port_field.text().strip() or "554")
        except ValueError:
            port = 554

        candidates = guess_rtsp_urls(
            ip=ip,
            username=self.user_field.text().strip(),
            password=self.pass_field.text(),
            port=port,
        )
        menu = QMenu(self)
        for u in candidates:
            act = menu.addAction(u)
            act.setData(u)

        chosen = menu.exec(self.guess_btn.mapToGlobal(self.guess_btn.rect().bottomLeft()))
        if chosen:
            val = chosen.data()
            if isinstance(val, str):
                self.url_field.setText(val)
                self.stream_type.setCurrentText("RTSP")
                self._log("Inserted candidate RTSP URL from templates.")

    def _stream_url(self) -> Optional[str]:
        mode = self.stream_type.currentText()
        url = self.url_field.text().strip()

        if mode == "AlfredCamera WebViewer":
            return None

        if url:
            return url

        host = self.host_field.text().strip()
        if not host:
            return None

        port = self.port_field.text().strip()
        username = self.user_field.text().strip()
        password = self.pass_field.text()

        if mode == "RTSP":
            try:
                port_i = int(port) if port else 554
            except ValueError:
                port_i = 554
            return guess_rtsp_urls(host, username=username, password=password, port=port_i)[0]

        if port:
            return f"http://{host}:{port}/"
        return f"http://{host}/"

    def _ensure_player(self) -> None:
        if self._player is not None:
            return
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        self._sink = QVideoSink(self)
        self._sink.videoFrameChanged.connect(self._on_frame)
        self._player.setVideoOutput(self._sink)
        if self._video_widget is not None:
            try:
                self._player.setVideoOutput(self._video_widget)
            except Exception:
                pass

        self._player.errorOccurred.connect(self._on_player_error)
        self._player.mediaStatusChanged.connect(self._on_media_status)

    def _connect(self) -> None:
        mode = self.stream_type.currentText()
        if mode == "AlfredCamera WebViewer":
            self._open_alfred()
            return

        url = self._stream_url()
        if not url:
            QMessageBox.warning(
                self,
                "Missing Stream",
                "Provide either a full stream URL, or a host (and port/user/pass if needed).",
            )
            return

        self._ensure_player()
        assert self._player is not None

        self._reconnect_attempts = 0
        self._set_status("connecting…")
        self._log(f"Connecting to: {url}")

        self._player.setSource(QUrl(url))
        self._player.play()

    def _disconnect(self) -> None:
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass
        self._set_status("disconnected")
        self._log("Disconnected.")

    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self._set_status("loaded")
        elif status == QMediaPlayer.MediaStatus.BufferedMedia:
            self._set_status("buffered")
        elif status == QMediaPlayer.MediaStatus.StalledMedia:
            self._set_status("stalled")
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._set_status("ended")
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._set_status("invalid media")

    def _on_player_error(self, err: QMediaPlayer.Error, error_string: str) -> None:
        self._set_status("error")
        self._log(f"Playback error: {error_string}")
        if not self._auto_reconnect:
            return
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self._log("Auto reconnect stopped (max attempts reached).")
            return
        self._reconnect_attempts += 1
        wait_ms = min(5000, 500 * self._reconnect_attempts)
        self._log(f"Retrying in {wait_ms} ms (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})…")
        QTimer.singleShot(wait_ms, self._connect)

    def _on_frame(self, frame) -> None:
        if not (self._motion_armed or self._tamper_armed):
            return
        try:
            img = frame.toImage()
        except Exception:
            return
        if img.isNull():
            return

        img = img.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        try:
            import numpy as _np  # type: ignore
            ptr = img.bits()
            ptr.setsize(img.sizeInBytes())
            arr = _np.frombuffer(ptr, dtype=_np.uint8).reshape((img.height(), img.width(), 4))
            gray = (0.299 * arr[:, :, 2] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 0]).astype(_np.uint8)
            mean_brightness = float(gray.mean())
        except Exception:
            w, h = img.width(), img.height()
            total = 0
            step = 4
            count = 0
            for y in range(0, h, step):
                for x in range(0, w, step):
                    c = img.pixelColor(x, y)
                    total += int(0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue())
                    count += 1
            if count <= 0:
                return
            mean_brightness = total / count
            gray = None

        now = time.time()
        cooldown = self._cooldown_seconds()

        if self._tamper_armed and mean_brightness < 12.0 and (now - self._last_motion_ts) > cooldown:
            self._last_motion_ts = now
            self._log("TAMPER: Scene is near-black (possible cover / blackout).")
            self._set_status("tamper alert")

        if not self._motion_armed:
            self._last_frame_gray = gray
            return

        if gray is None:
            return

        if self._last_frame_gray is None:
            self._last_frame_gray = gray
            return

        try:
            import numpy as _np  # type: ignore
            diff = _np.abs(gray.astype(_np.int16) - self._last_frame_gray.astype(_np.int16)).astype(_np.uint8)
            changed = float((diff > 18).mean())
        except Exception:
            self._last_frame_gray = gray
            return

        self._last_frame_gray = gray
        if changed >= self._motion_threshold() and (now - self._last_motion_ts) > cooldown:
            self._last_motion_ts = now
            self._log(f"MOTION: change={changed:.3f} (threshold={self._motion_threshold():.3f})")
            self._set_status("motion detected")

    def _snapshot(self) -> None:
        if self._sink is None:
            QMessageBox.information(self, "Snapshot", "Connect to a camera first.")
            return
        frame = self._sink.videoFrame()
        if frame is None or not frame.isValid():
            QMessageBox.information(self, "Snapshot", "No video frame available yet.")
            return
        img = frame.toImage()
        if img.isNull():
            QMessageBox.information(self, "Snapshot", "Snapshot failed (invalid image).")
            return

        out_dir = Path.home() / "NetNinja_Snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = time.strftime("snapshot_%Y%m%d_%H%M%S.png")
        out_path = out_dir / fname
        ok = img.save(str(out_path))
        if ok:
            self._log(f"Saved snapshot: {out_path}")
            QMessageBox.information(self, "Snapshot Saved", f"Saved to:\n{out_path}")
        else:
            QMessageBox.warning(self, "Snapshot", "Failed to save snapshot.")

    def _open_alfred(self) -> None:
        url = "https://alfred.camera/webapp/viewer"
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
            if not hasattr(self, "_alfred_web"):
                self._alfred_web = QWebEngineView(self.alfred_container)  # type: ignore[attr-defined]
                self.alfred_container.layout().addWidget(self._alfred_web)  # type: ignore[union-attr]
            self._alfred_web.setUrl(QUrl(url))  # type: ignore[attr-defined]
            self._set_status("Alfred WebViewer open")
            self._log("Opened Alfred WebViewer (embedded).")
        except Exception:
            QDesktopServices.openUrl(QUrl(url))
            self._set_status("Alfred WebViewer opened in browser")
            self._log("Opened Alfred WebViewer in external browser (Qt WebEngine not available).")



class ToolsTab(CategoryTab):
    """TOOLS tab for system and network utilities."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.main_window = main_window
        self.add_panel("System Tools", self.build_system_tools())
        self.add_panel("Network Tools", self.build_network_tools())

    def build_system_tools(self) -> QGroupBox:
        group = self.add_group("System Tools", "System information and diagnostics.")
        layout = QGridLayout()

        if self.main_window.capabilities.is_windows:
            tools = [
                ("System Info", "systeminfo", "System info"),
                ("Task List", "tasklist", "Task list"),
                ("Network Stats", "netstat -ano", "Network stats"),
                ("IP Config", "ipconfig /all", "IP config"),
            ]
        else:
            tools = [
                ("System Info", "uname -a", "System info"),
                ("Task List", "ps -eo pid,comm,pcpu,pmem --sort=-pcpu", "Task list"),
                ("Network Stats", "ss -s", "Network stats"),
                ("IP Config", "ip addr", "IP config"),
            ]

        for idx, (label, cmd, desc) in enumerate(tools):
            btn = create_glowing_button(label, lambda c=cmd, d=desc: self.executor(c, d))
            required = self.main_window._infer_required_tools(cmd)
            self.main_window.guard_button(btn, required_tools=required)
            layout.addWidget(btn, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        return group

    def build_network_tools(self) -> QGroupBox:
        group = self.add_group("Network Tools", "Network diagnostics and testing.")
        layout = QGridLayout()

        if self.main_window.capabilities.is_windows:
            tools = [
                ("Route Table", "route print", "Route table"),
                ("ARP Table", "arp -a", "ARP table"),
                ("DNS Cache", "ipconfig /displaydns", "DNS cache"),
                ("Firewall Status", "netsh advfirewall show allprofiles", "Firewall status"),
            ]
        else:
            firewall_cmd = "ufw status" if shutil.which("ufw") else "iptables -S"
            tools = [
                ("Route Table", "ip route", "Route table"),
                ("ARP Table", "ip neigh", "ARP table"),
                ("DNS Cache", "resolvectl statistics", "DNS cache"),
                ("Firewall Status", firewall_cmd, "Firewall status"),
            ]

        for idx, (label, cmd, desc) in enumerate(tools):
            btn = create_glowing_button(label, lambda c=cmd, d=desc: self.executor(c, d))
            required = self.main_window._infer_required_tools(cmd)
            require_admin = cmd.startswith("iptables")
            self.main_window.guard_button(btn, required_tools=required, require_admin=require_admin)
            layout.addWidget(btn, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        return group


class NetReaperGui(QWidget):
    """Main container that stitches tabs, logs, and history."""

    def __init__(self):
        super().__init__()
        self.capabilities = detect_capabilities()
        self.provider = get_provider(self.capabilities)
        self.job_manager = JobManager(self._append_log_line)
        self.job_manager.event_emitted.connect(self._handle_job_event)
        self.job_manager.result_emitted.connect(self._handle_job_result)
        self.active_jobs: set[str] = set()
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self.setWindowTitle("NetReaper Command Center")
        self.setMinimumSize(1200, 720)
        self.session_id = uuid4().hex[:8].upper()
        self.ingress_online = False
        self.target_fields: List[TargetField] = []
        self.target_history: List[str] = []
        self.bssid_fields: List[TargetField] = []
        self.bssid_history: List[str] = []
        self.feature_controls: Dict[str, List[QPushButton]] = {}
        self.active_jobs: set[str] = set()
        self.wiring_flags = {}
        self.lite_mode = False
        self.custom_wordlist = ""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Menu bar
        self.menu_bar = QMenuBar()
        diagnostics_menu = self.menu_bar.addMenu("Diagnostics")
        self.self_test_action = QAction("Run Self Test", self)
        self.self_test_action.triggered.connect(self.run_self_test)
        diagnostics_menu.addAction(self.self_test_action)
        self.save_diag_action = QAction("Save Diagnostics", self)
        self.save_diag_action.triggered.connect(self.save_diagnostics)
        diagnostics_menu.addAction(self.save_diag_action)
        main_layout.addWidget(self.menu_bar)

        # Toolbar
        self.toolbar = QToolBar("Actions")
        # Match reference: a slim text-only command strip.
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        clear_log_action = QAction("Clear log", self)
        clear_log_action.triggered.connect(self.clear_log)
        self.wiring_flags["clear_log_action"] = True
        self.toolbar.addAction(clear_log_action)
        self.toolbar.addSeparator()
        refresh_status_action = QAction("Show status", self)
        refresh_status_action.triggered.connect(lambda: self.submit_command_job("netreaper status", "Status"))
        if not (shutil.which("netreaper") or self.capabilities.tools.get("netreaper", False)):
            refresh_status_action.setEnabled(False)
            refresh_status_action.setToolTip("Missing tool: netreaper")
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

        # Ensure the window width can display the header exactly as designed (no scaling/distortion).
        try:
            ref = self.reaper_header.reference_size()
            self.setMinimumWidth(max(self.minimumWidth(), ref.width()))
            if self.width() < ref.width():
                self.resize(ref.width(), self.height())
        except Exception:
            pass


        self.hud_panel = HUDPanel()
        main_layout.addWidget(self.hud_panel)

        central_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_splitter.setChildrenCollapsible(False)

        nav_container = QFrame()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(8)
        nav_label = QLabel("Quick Actions")
        nav_label.setStyleSheet("font-weight: 700;")
        nav_layout.addWidget(nav_label)

        # Internal navigation list (kept for keyboard navigation / state tracking).
        # The reference UI does not expose this list visually.
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setVisible(False)
        nav_layout.addWidget(self.nav_list)

        def add_quick_action(label: str, handler) -> None:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            # Styled by QSS to match reference "Quick Actions" pill buttons.
            btn.setProperty("quickAction", "true")
            nav_layout.addWidget(btn)

        add_quick_action("Console Focus", lambda: self.output_log.setFocus())
        add_quick_action("History Focus", lambda: self.history_list.setFocus())
        add_quick_action("Clear Log", self.clear_log)
        add_quick_action("Stop Tasks", self.stop_all_tasks)
        add_quick_action("Toggle Lite Mode", lambda: self.toggle_lite_mode(not self.lite_mode))
        add_quick_action("Edit Config", self.edit_config)
        add_quick_action("Select Wordlist", self.select_wordlist)
        nav_layout.addStretch()
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

        self.scan_tab = ScanTab(self.submit_command_job, self)
        self.recon_tab = ReconTab(self.submit_command_job, self)
        self.wireless_tab = WirelessTab(self.submit_command_job, self)
        self.web_tab = WebTab(self.submit_command_job, self)
        self.camera_tab = IPCameraTab(self)
        self.tools_tab = ToolsTab(self.submit_command_job, self)
        self.wizard_tab = WizardTab(self.submit_command_job, self)
        self.jobs_tab = JobsTab(self.job_manager, self.save_diagnostics, self.run_self_test, self)

        wizard_page = self._wrap_in_workspace("Automation Wizards", self.wizard_tab)
        jobs_page = self._wrap_in_workspace("Diagnostics & Jobs", self.jobs_tab)

        self.pages = [
            ("Scan", self.scan_tab),
            ("Recon", self.recon_tab),
            ("Wireless", self.wireless_tab),
            ("Web", self.web_tab),
            ("Cameras", self.camera_tab),
            ("Tools", self.tools_tab),
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
        self.reaper_header.add_nav_button("Cameras", lambda: self.navigate_to("Cameras"))
        self.reaper_header.add_nav_button("Tools", lambda: self.navigate_to("Tools"))
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
        self._append_log_line(
            f"[cap] Platform: {self.capabilities.platform} | Admin: {self.capabilities.is_admin} | WSL: {self.capabilities.tools.get('wsl', False)}"
        )
        self._append_log_line(f"[cap] Features: {', '.join(sorted([k for k, v in self.capabilities.feature_flags.items() if v]))}")
        self.run_ui_debug_checks()

    def build_operations_deck(self) -> QWidget:
        deck = QSplitter(Qt.Orientation.Horizontal)
        deck.setChildrenCollapsible(False)

        self.output_panel = PanelWindow("Advanced Details", "Raw command output and controls")
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
        self.output_panel.toggle_collapse()
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

    def _append_log_line(self, line: str) -> None:
        if hasattr(self, "output_log") and self.output_log:
            self.output_log.appendPlainText(line)

    def _handle_job_event(self, event: Dict[str, Any]) -> None:
        job_id = event.get("job_id", "")
        event_type = event.get("type")
        if event_type == "JOB_START":
            if job_id:
                self.active_jobs.add(job_id)
            self.ingress_online = True
        elif event_type in ("JOB_END", "JOB_FAIL"):
            if job_id in self.active_jobs:
                self.active_jobs.remove(job_id)
            if not self.active_jobs:
                self.ingress_online = False
        elif event_type == "PRECHECK_FAIL":
            detail = event.get("detail", {})
            reason = detail.get("reason", "Action unavailable")
            guidance = detail.get("guidance", "")
            QMessageBox.warning(self, "Action unavailable", f"{reason}\n{guidance}".strip())
        self.refresh_reaper_header()

    def _handle_job_result(self, result: Dict[str, Any]) -> None:
        status = result.get("status", "")
        returncode = result.get("returncode", "")
        self.output_status_label.setText(f"Status: {status} (code {returncode})")
        color = "#3dd598" if status == "success" else "#ff7b7b"
        if hasattr(self, "output_panel"):
            self.output_panel.set_status(color)
        if hasattr(self, "history_panel"):
            self.history_panel.set_status(color)

    def feature_status(self, feature_key: str) -> Dict[str, object]:
        return self.capabilities.feature_support.get(feature_key, {})

    def _register_feature_control(self, feature_key: str, button: QPushButton) -> None:
        if not hasattr(self, "feature_controls"):
            self.feature_controls = {}
        controls = self.feature_controls.setdefault(feature_key, [])
        if button not in controls:
            controls.append(button)

    def _apply_support_badge(self, button: QPushButton, badge: str) -> None:
        base_text = button.property("baseText")
        if not base_text:
            base_text = button.text()
            button.setProperty("baseText", base_text)
        if badge:
            button.setText(f"{base_text} [{badge}]")
        else:
            button.setText(base_text)

    def apply_feature_support(self, button: QPushButton, feature_key: str) -> None:
        status = self.feature_status(feature_key)
        if not status:
            return
        self._register_feature_control(feature_key, button)
        badge = status.get("badge", "")
        self._apply_support_badge(button, badge)
        parts: List[str] = []
        reason = str(status.get("reason", "")).strip()
        notes = str(status.get("notes", "")).strip()
        recommended = str(status.get("recommended_path", "")).strip()
        if reason:
            parts.append(reason)
        if notes:
            parts.append(notes)
        if recommended:
            parts.append(f"Recommended path: {recommended}")
        tooltip = " ".join(parts).strip()
        if tooltip:
            button.setToolTip(tooltip)
        base_support = status.get("base_support", "")
        enabled = bool(status.get("enabled", True))
        if not enabled or base_support in ("unsupported", "external_required"):
            button.setEnabled(False)

    def guard_button(
        self,
        button: QPushButton,
        *,
        required_tools: Optional[List[str]] = None,
        require_admin: bool = False,
        feature_flag: Optional[str] = None,
        guidance: str = "",
    ) -> None:
        allowed = True
        reason = ""
        if feature_flag and not self.capabilities.flag(feature_flag):
            allowed = False
            reason = self.capabilities.reason(feature_flag) or "Capability not available"
        if required_tools:
            for tool in required_tools:
                if not tool:
                    continue
                available = self.capabilities.tools.get(tool, False) or shutil.which(tool) is not None
                if not available:
                    if self.capabilities.is_windows and self.capabilities.tools.get("wsl", False):
                        reason = f"Requires WSL tool: {tool}"
                        continue
                    allowed = False
                    reason = f"Missing tool: {tool}"
                    break
        if require_admin and not self.capabilities.is_admin:
            allowed = False
            reason = "Requires administrator/root privileges"
        if not allowed:
            button.setEnabled(False)
            tip = reason if not guidance else f"{reason}. {guidance}"
            button.setToolTip(tip)
        elif reason:
            button.setToolTip(reason if not guidance else f"{reason}. {guidance}")

    def _should_use_powershell(self, command: str) -> bool:
        if not self.capabilities.is_windows:
            return False
        head = command.strip()
        if head.startswith(("Get-", "Set-", "New-", "Test-", "Invoke-")):
            return True
        if "|" in head or "$" in head:
            return True
        return False

    def _infer_required_tools(self, command: str) -> List[str]:
        try:
            tokens = shlex.split(command, posix=not self.capabilities.is_windows)
        except ValueError:
            return []
        if not tokens:
            return []
        if tokens[0] == "sudo":
            tokens = tokens[1:]
        if tokens and tokens[0] == "timeout":
            tokens = tokens[1:]
        return tokens[:1]

    def closeEvent(self, event) -> None:
        try:
            if hasattr(self, "scan_tab"):
                self.scan_tab._save_discovery_splitter_state()
        except Exception as exc:
            self._append_log_line(f"[settings] Splitter save failed on close: {exc}")
        super().closeEvent(event)

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

    def scan_targets_for_field(self, field: TargetField) -> None:
        def precheck() -> tuple[bool, str, str]:
            if not self.capabilities.flag("can_list_interfaces"):
                reason = self.capabilities.reason("can_list_interfaces") or "Interface discovery unavailable"
                return False, reason, "Install required tools or run with elevated privileges."
            return True, "", ""

        def execute() -> ExecutionResult:
            start = time.time()
            interfaces = self.provider.get_interfaces()
            return ExecutionResult(returncode=0, payload={"interfaces": interfaces}, elapsed=time.time() - start)

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            interfaces = result.payload.get("interfaces", [])
            ips: List[str] = []
            for it in interfaces:
                ipv4 = getattr(it, "ipv4", []) if not isinstance(it, dict) else it.get("ipv4", [])
                if isinstance(ipv4, list):
                    ips.extend(ipv4)
            summary = {"ips": len(ips)}
            return {"summary": summary, "items": [], "ips": ips}

        def ui_update(payload: Dict[str, Any]) -> None:
            ips = payload.get("ips", [])
            if ips:
                for ip in ips:
                    if ip not in self.target_history:
                        self.target_history.append(ip)
                field.set_history(self.target_history)
                for target_field in self.target_fields:
                    target_field.set_history(self.target_history)
                self._append_log_line(f"[targets] Found IPs: {', '.join(ips)}")
            else:
                self._append_log_line("[targets] No local IPs discovered.")

        job = JobSpec(
            name="Scan Local Targets",
            category="discovery",
            precheck=precheck,
            execute=execute,
            parse=parse,
            ui_update=ui_update,
        )
        self.job_manager.run_job(job)

    def start_discovery(self) -> None:
        """Run interface/Wi-Fi/neighbor discovery and update Scan tab + holo map."""
        scan_tab = getattr(self, "scan_tab", None)
        if scan_tab is None or not hasattr(scan_tab, "update_discovery"):
            QMessageBox.warning(self, "Discovery unavailable", "Scan tab is not ready for discovery updates.")
            return

        def precheck() -> tuple[bool, str, str]:
            flags = self.capabilities.feature_flags
            if not any(
                flags.get(key, False)
                for key in (
                    "can_list_interfaces",
                    "can_show_routes",
                    "can_list_sockets",
                    "can_read_neighbors",
                    "can_scan_wifi",
                    "can_host_discovery_quick",
                )
            ):
                return False, "No discovery capabilities available", "Install required tools or run with elevated privileges."
            return True, "", ""

        def execute() -> ExecutionResult:
            start = time.time()
            errors: List[str] = []
            interfaces: List[InterfaceRecord] = []
            routes: List[RouteRecord] = []
            sockets: List[SocketRecord] = []
            neighbors: List[NeighborRecord] = []
            aps: List[WifiAPRecord] = []
            hosts: List[HostRecord] = []

            if self.capabilities.flag("can_list_interfaces"):
                try:
                    interfaces = self.provider.get_interfaces()
                except Exception as exc:
                    errors.append(f"Interface discovery failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_list_interfaces"))

            if self.capabilities.flag("can_show_routes"):
                try:
                    routes = self.provider.get_routes()
                except Exception as exc:
                    errors.append(f"Route discovery failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_show_routes"))

            if self.capabilities.flag("can_list_sockets"):
                try:
                    sockets = self.provider.get_sockets()
                except Exception as exc:
                    errors.append(f"Socket discovery failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_list_sockets"))

            if self.capabilities.flag("can_read_neighbors"):
                try:
                    neighbors = self.provider.get_neighbors()
                except Exception as exc:
                    errors.append(f"Neighbor discovery failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_read_neighbors"))

            if self.capabilities.flag("can_scan_wifi"):
                try:
                    aps = self.provider.scan_wifi()
                except Exception as exc:
                    errors.append(f"Wi-Fi scan failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_scan_wifi"))

            if self.capabilities.flag("can_host_discovery_quick"):
                try:
                    hosts = self.provider.discover_hosts_quick()
                except Exception as exc:
                    errors.append(f"Host discovery failed: {exc}")
            else:
                errors.append(self.capabilities.reason("can_host_discovery_quick"))

            payload = {
                "interfaces": interfaces,
                "routes": routes,
                "sockets": sockets,
                "neighbors": neighbors,
                "aps": aps,
                "hosts": hosts,
                "errors": [e for e in errors if e],
            }
            return ExecutionResult(returncode=0, payload=payload, elapsed=time.time() - start)

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            payload = result.payload or {}
            negative = payload.get("negative", {})
            negative_errors = (
                len(negative.get("ui_errors", []))
                + len(negative.get("probe_errors", []))
                + (1 if negative.get("missing_tool_check", {}).get("status") == "fail" else 0)
            )
            summary = {
                "interfaces": len(payload.get("interfaces", [])),
                "routes": len(payload.get("routes", [])),
                "sockets": len(payload.get("sockets", [])),
                "neighbors": len(payload.get("neighbors", [])),
                "wifi": len(payload.get("aps", [])),
                "hosts": len(payload.get("hosts", [])),
                "errors": len(payload.get("errors", [])),
                "disabled_features": len(negative.get("disabled_features", [])),
                "negative_errors": negative_errors,
            }
            return {
                **payload,
                "summary": summary,
                "counts": summary,
                "items": [],
            }

        def ui_update(payload: Dict[str, Any]) -> None:
            scan_tab.update_discovery(payload)
            interfaces = payload.get("interfaces", [])
            ips = []
            for it in interfaces:
                ipv4 = getattr(it, "ipv4", []) if not isinstance(it, dict) else it.get("ipv4", [])
                if isinstance(ipv4, list):
                    ips.extend(ipv4)
            if ips:
                for ip in ips:
                    if ip not in self.target_history:
                        self.target_history.append(ip)
                for field in self.target_fields:
                    field.set_history(self.target_history)

        job = JobSpec(
            name="Network Discovery",
            category="discovery",
            precheck=precheck,
            execute=execute,
            parse=parse,
            ui_update=ui_update,
        )
        self.job_manager.run_job(job)


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
            except OSError as exc:
                self._append_log_line(f"[history] Failed to save BSSID history: {exc}")

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

    def save_diagnostics(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save diagnostics",
            os.path.expanduser("~/netreaper_diagnostics.json"),
            "JSON files (*.json);;All files (*.*)",
        )
        if not path:
            return
        context = {
            "platform": self.capabilities.platform,
            "is_windows": self.capabilities.is_windows,
            "is_linux": self.capabilities.is_linux,
            "is_wsl": self.capabilities.is_wsl,
            "is_admin": self.capabilities.is_admin,
            "tools": self.capabilities.tools,
            "features": self.capabilities.feature_flags,
            "feature_matrix": self.capabilities.feature_matrix,
            "feature_support": self.capabilities.feature_support,
            "job_history": self.job_manager.job_history,
        }
        try:
            self.job_manager.export_diagnostics(path, context)
            self._append_log_line(f"[diag] Saved diagnostics to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Diagnostics failed", f"Failed to save diagnostics: {exc}")

    def _run_blocked_feature_probes(self, feature_keys: List[str], timeout_s: float = 4.0) -> List[Dict[str, Any]]:
        if not feature_keys:
            return []
        job_feature_map: Dict[str, str] = {}
        pending: List[str] = []
        events: Dict[str, List[Dict[str, Any]]] = {}
        results: List[Dict[str, Any]] = []
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)

        def on_event(event: Dict[str, Any]) -> None:
            job_id = event.get("job_id")
            if job_id in pending:
                events[job_id].append(event)

        def on_result(result: Dict[str, Any]) -> None:
            job_id = result.get("job_id")
            if job_id in pending:
                pending.remove(job_id)
            if not pending:
                loop.quit()

        self.job_manager.event_emitted.connect(on_event)
        self.job_manager.result_emitted.connect(on_result)

        for feature_key in feature_keys:
            status = self.feature_status(feature_key)
            reason = str(status.get("reason", "Feature unavailable"))
            guidance = str(status.get("recommended_path", ""))

            def precheck(reason=reason, guidance=guidance) -> tuple[bool, str, str]:
                return False, reason, guidance

            def execute() -> ExecutionResult:
                return ExecutionResult(returncode=1, error="Probe executed unexpectedly")

            def parse(_result: ExecutionResult) -> Dict[str, Any]:
                return {"summary": {"probe": True}, "counts": {}, "items": []}

            def ui_update(_payload: Dict[str, Any]) -> None:
                return

            job = JobSpec(
                name=f"Self-test probe: {feature_key}",
                category="diagnostics",
                precheck=precheck,
                execute=execute,
                parse=parse,
                ui_update=ui_update,
                feature_key=feature_key,
            )
            job_feature_map[job.job_id] = feature_key
            pending.append(job.job_id)
            events[job.job_id] = []
            self.job_manager.run_job(job)

        timer.timeout.connect(loop.quit)
        QApplication.processEvents()
        if pending:
            timer.start(int(timeout_s * 1000))
            loop.exec()
            timer.stop()

        self.job_manager.event_emitted.disconnect(on_event)
        self.job_manager.result_emitted.disconnect(on_result)

        for job_id in job_feature_map:
            events.setdefault(job_id, [])

        for job_id, event_list in events.items():
            feature_key = job_feature_map.get(job_id, "")
            event_types = [event.get("type", "") for event in event_list]
            blocked_event = next((event for event in event_list if event.get("type") == "BLOCKED_BY_CAPABILITY"), None)
            blocked_detail = blocked_event.get("detail", {}) if blocked_event else {}
            results.append(
                {
                    "feature_key": feature_key,
                    "job_id": job_id,
                    "event_types": event_types,
                    "blocked_event": bool(blocked_event),
                    "blocked_reason": blocked_detail.get("reason", ""),
                    "blocked_guidance": blocked_detail.get("guidance", ""),
                    "exec_started": "EXEC_START" in event_types,
                    "timed_out": job_id in pending,
                }
            )
        return results

    def run_self_test(self) -> None:
        """Run provider self-tests and update discovery views."""
        scan_tab = getattr(self, "scan_tab", None)
        if scan_tab is None or not hasattr(scan_tab, "update_discovery"):
            QMessageBox.warning(self, "Self test unavailable", "Scan tab is not ready for diagnostics.")
            return

        disabled_features = {
            key: status
            for key, status in self.capabilities.feature_support.items()
            if not status.get("enabled", True)
        }
        ui_checks: List[Dict[str, Any]] = []
        ui_errors: List[str] = []
        missing_tool_hits: List[str] = []
        missing_tool_errors: List[str] = []
        for feature_key, controls in getattr(self, "feature_controls", {}).items():
            status = disabled_features.get(feature_key)
            if not status:
                continue
            reason = str(status.get("reason", "")).strip()
            recommended = str(status.get("recommended_path", "")).strip()
            badge = str(status.get("badge", "")).strip()
            for control in controls:
                tooltip = control.toolTip() or ""
                text = control.text()
                enabled = control.isEnabled()
                ui_checks.append(
                    {
                        "feature_key": feature_key,
                        "control_text": text,
                        "enabled": enabled,
                        "tooltip": tooltip,
                    }
                )
                if enabled:
                    ui_errors.append(f"{feature_key} control still enabled: {text}")
                if reason and reason not in tooltip:
                    ui_errors.append(f"{feature_key} tooltip missing reason: {text}")
                if recommended and recommended not in tooltip:
                    ui_errors.append(f"{feature_key} tooltip missing recommendation: {text}")
                if badge and badge not in text:
                    ui_errors.append(f"{feature_key} badge missing: {text}")
                if "Missing tool" in reason:
                    if "Missing tool" in tooltip:
                        missing_tool_hits.append(feature_key)
                    else:
                        missing_tool_errors.append(f"{feature_key} tooltip missing missing-tool reason.")

        if missing_tool_errors:
            missing_tool_check = {"status": "fail", "detail": "; ".join(missing_tool_errors)}
        elif missing_tool_hits:
            missing_tool_check = {"status": "pass", "detail": "Missing-tool messaging present."}
        else:
            missing_tool_check = {"status": "skipped", "detail": "No missing-tool features detected."}

        probe_features = [key for key in disabled_features.keys() if key in getattr(self, "feature_controls", {})]
        probe_results = self._run_blocked_feature_probes(probe_features)
        probe_errors = []
        for probe in probe_results:
            if not probe.get("blocked_event"):
                probe_errors.append(f"{probe.get('feature_key')} missing BLOCKED_BY_CAPABILITY event")
            if probe.get("exec_started"):
                probe_errors.append(f"{probe.get('feature_key')} executed despite being blocked")
            if probe.get("timed_out"):
                probe_errors.append(f"{probe.get('feature_key')} probe timed out")

        def execute() -> ExecutionResult:
            start = time.time()
            errors: List[str] = []
            payload: Dict[str, Any] = {
                "interfaces": [],
                "routes": [],
                "sockets": [],
                "neighbors": [],
                "aps": [],
                "hosts": [],
                "errors": [],
                "negative": {
                    "disabled_features": list(disabled_features.keys()),
                    "ui_checks": ui_checks,
                    "ui_errors": ui_errors,
                    "probe_results": probe_results,
                    "probe_errors": probe_errors,
                    "missing_tool_check": missing_tool_check,
                },
            }

            tests = [
                ("interfaces", self.provider.get_interfaces, ["name", "state", "mac"]),
                ("routes", self.provider.get_routes, ["destination", "gateway", "interface"]),
                ("sockets", self.provider.get_sockets, ["proto", "local_address", "remote_address"]),
                ("neighbors", self.provider.get_neighbors, ["ip", "mac", "state"]),
                ("aps", self.provider.scan_wifi, ["ssid", "bssid", "channel"]),
                ("hosts", self.provider.discover_hosts_quick, ["ip", "state"]),
            ]

            for key, fn, required_fields in tests:
                try:
                    records = fn()
                    payload[key] = records
                    for idx, record in enumerate(records):
                        for field in required_fields:
                            value = getattr(record, field, None) if not isinstance(record, dict) else record.get(field)
                            if value is None:
                                errors.append(f"{key}[{idx}] missing field: {field}")
                except Exception as exc:
                    errors.append(f"{key} test failed: {exc}")

            if ui_errors:
                errors.extend(ui_errors)
            if probe_errors:
                errors.extend(probe_errors)
            if missing_tool_check.get("status") == "fail":
                errors.append(missing_tool_check.get("detail", "Missing-tool check failed"))

            payload["errors"] = errors
            return ExecutionResult(returncode=0 if not errors else 1, payload=payload, elapsed=time.time() - start)

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            payload = result.payload or {}
            summary = {
                "interfaces": len(payload.get("interfaces", [])),
                "routes": len(payload.get("routes", [])),
                "sockets": len(payload.get("sockets", [])),
                "neighbors": len(payload.get("neighbors", [])),
                "wifi": len(payload.get("aps", [])),
                "hosts": len(payload.get("hosts", [])),
                "errors": len(payload.get("errors", [])),
            }
            return {
                **payload,
                "summary": summary,
                "counts": summary,
                "items": [],
            }

        def ui_update(payload: Dict[str, Any]) -> None:
            scan_tab.update_discovery(payload)

        job = JobSpec(
            name="Self Test",
            category="diagnostics",
            execute=execute,
            parse=parse,
            ui_update=ui_update,
        )
        self.job_manager.run_job(job)

    def _run_command_subprocess(
        self,
        command: str,
        job_id: str,
        *,
        use_powershell: bool,
        is_linux_command: bool,
        timeout: int,
        requires_admin: bool,
    ) -> ExecutionResult:
        start = time.time()
        run_command = command
        if requires_admin and self.capabilities.is_admin and not shutil.which("sudo"):
            if run_command.startswith("sudo"):
                run_command = run_command[len("sudo"):].strip()

        env = os.environ.copy()
        if self.lite_mode:
            env["NR_LITE_MODE"] = "1"
        if self.custom_wordlist:
            env["DEFAULT_WORDLIST"] = self.custom_wordlist

        if is_linux_command:
            cmd_list = ["wsl", "-e"] + shlex.split(run_command)
        elif use_powershell:
            cmd_list = ["powershell", "-NoProfile", "-Command", run_command]
        else:
            cmd_list = shlex.split(run_command)

        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            creationflags=creationflags,
        )
        self._active_processes[job_id] = process
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            returncode = 1
            return ExecutionResult(
                returncode=returncode,
                stdout=stdout.splitlines(),
                stderr=stderr.splitlines(),
                error="Command timed out",
                elapsed=time.time() - start,
            )
        finally:
            self._active_processes.pop(job_id, None)

        return ExecutionResult(
            returncode=returncode,
            stdout=stdout.splitlines(),
            stderr=stderr.splitlines(),
            elapsed=time.time() - start,
        )

    def submit_command_job(
        self,
        command: str,
        description: str,
        target: Optional[str] = None,
        *,
        use_powershell: Optional[bool] = None,
        is_linux_command: bool = False,
        timeout: int = 120,
        feature_key: Optional[str] = None,
    ) -> Optional[str]:
        """Submit a command as a JobSpec so lifecycle events are consistent."""
        command = command.strip()
        if not command:
            QMessageBox.warning(self, "Empty command", "No command provided")
            return None

        use_powershell = self._should_use_powershell(command) if use_powershell is None else use_powershell
        required_tools = [] if use_powershell else self._infer_required_tools(command)
        requires_admin = command.startswith("sudo")
        if self.capabilities.is_windows and not is_linux_command and required_tools:
            if not shutil.which(required_tools[0]) and self.capabilities.tools.get("wsl", False):
                is_linux_command = True

        def precheck() -> tuple[bool, str, str]:
            if feature_key:
                status = self.feature_status(feature_key)
                if status and not status.get("enabled", True):
                    reason = status.get("reason", "Feature unavailable")
                    guidance = status.get("recommended_path", "")
                    return False, reason, guidance
            if is_linux_command and not self.capabilities.tools.get("wsl", False):
                return False, "WSL not available", "Install WSL to run Linux commands."
            if requires_admin and not self.capabilities.is_admin:
                return False, "Requires administrator/root privileges", "Rerun the GUI as admin/root."
            if use_powershell and not (self.capabilities.tools.get("powershell", False) or shutil.which("powershell")):
                return False, "PowerShell not available", "Install or enable PowerShell."
            if required_tools and not is_linux_command:
                for tool in required_tools:
                    if not tool:
                        continue
                    if not (self.capabilities.tools.get(tool, False) or shutil.which(tool)):
                        return False, f"Missing tool: {tool}", "Install the required tool and try again."
            return True, "", ""

        def execute() -> ExecutionResult:
            return self._run_command_subprocess(
                command,
                job_id,
                use_powershell=use_powershell,
                is_linux_command=is_linux_command,
                timeout=timeout,
                requires_admin=requires_admin,
            )

        def parse(result: ExecutionResult) -> Dict[str, Any]:
            summary = {
                "returncode": result.returncode,
                "stdout_lines": len(result.stdout),
                "stderr_lines": len(result.stderr),
            }
            return {
                "summary": summary,
                "counts": summary,
                "items": [],
            }

        def ui_update(payload: Dict[str, Any]) -> None:
            status = "success" if payload.get("summary", {}).get("returncode", 1) == 0 else "failed"
            self.output_status_label.setText(f"Status: {status} ({description})")

        job_id = uuid4().hex[:8].upper()
        if target:
            self.add_target_history(target)

        log_command = self.sanitize_command_for_display(command)
        self.current_command_label.setText(f"Command: {log_command}")
        self.output_status_label.setText(f"Status: running ({description})")
        if hasattr(self, "output_panel"):
            self.output_panel.set_status("#5ad6ff")
        self._append_log_line(f"[{description}] $ {log_command}")

        item = QListWidgetItem(f"{description}: {log_command}")
        item.setData(Qt.ItemDataRole.UserRole, command)
        self.history_list.addItem(item)
        self.history_panel.set_status("#5ad6ff")

        job = JobSpec(
            name=description,
            category="command",
            precheck=precheck,
            execute=execute,
            parse=parse,
            ui_update=ui_update,
            job_id=job_id,
            feature_key=feature_key,
        )
        self.job_manager.run_job(job)
        return job_id

    def sanitize_command_for_display(self, command: str) -> str:
        """Redact sensitive information from commands before logging or displaying."""
        return sanitize_command_for_display(command)

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
            self.submit_command_job(command, "Re-run")

    def refresh_reaper_header(self) -> None:
        target = ""
        if self.target_fields:
            target = self.target_fields[0].value()
        self.reaper_header.update_stats(
            self.session_id,
            target,
            self.ingress_online,
            len(self.active_jobs),
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
            self.submit_command_job(cmd, "Manual Command")
            self.cmd_input.clear()

    def stop_all_tasks(self) -> None:
        """Terminate running command processes and clear active jobs."""
        if not self._active_processes:
            self._append_log_line("[info] No active tasks to stop")
            return
        self._append_log_line("[info] Stopping all active tasks...")
        for job_id, process in list(self._active_processes.items()):
            try:
                if sys.platform == "win32":
                    process.kill()
                else:
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except Exception as exc:
                        process.kill()
                        self._append_log_line(f"[warn] Force-killed job {job_id}: {exc}")
            except Exception as exc:
                self._append_log_line(f"[warn] Failed to stop job {job_id}: {exc}")
        self._active_processes.clear()
        self.active_jobs.clear()
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
