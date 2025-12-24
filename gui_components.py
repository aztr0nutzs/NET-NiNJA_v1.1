"""
Reusable GUI components shared by the NetReaper Linux and Windows interfaces.

Includes:
* PanelWindow: embedded sub-window widget with header controls.
* PanelWorkspacePage: simple grid manager for arranging panels.
"""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PanelWindow(QWidget):
    """A reusable embedded sub-window with a header and animated collapse."""

    request_maximize = pyqtSignal(object)
    request_restore = pyqtSignal(object)

    def __init__(self, title: str, description: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("panelWindow")
        self._content: Optional[QWidget] = None
        self._workspace = None
        self._collapsed = False
        self._hidden = False
        self._floating_window: Optional[QDialog] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        self.header = QFrame()
        self.header.setObjectName("panelHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(10)

        self.status_light = QFrame()
        self.status_light.setObjectName("statusLight")
        self.status_light.setFixedSize(14, 14)
        header_layout.addWidget(self.status_light)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(description)
        self.subtitle_label.setStyleSheet("color: #8fb2d9; font-size: 10px;")
        header_layout.addWidget(self.subtitle_label, 1)

        self.btn_collapse = self._make_header_button("–", self.toggle_collapse)
        self.btn_maximize = self._make_header_button("⬒", self.toggle_maximize)
        self.btn_detach = self._make_header_button("⇱", self.toggle_detach)
        self.btn_hide = self._make_header_button("⤬", self.toggle_hide)
        header_layout.addWidget(self.btn_collapse)
        header_layout.addWidget(self.btn_maximize)
        header_layout.addWidget(self.btn_detach)
        header_layout.addWidget(self.btn_hide)
        outer.addWidget(self.header)
        self._status_color = "#3dd598"
        self.set_status(self._status_color)

        self.content_area = QFrame()
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(8)
        outer.addWidget(self.content_area)

        self._collapse_anim = QPropertyAnimation(self.content_area, b"maximumHeight", self)
        self._collapse_anim.setDuration(220)
        self._collapse_anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutCubic))

    def _make_header_button(self, text: str, handler) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("panelButton", True)
        btn.setFixedWidth(26)
        btn.clicked.connect(handler)
        return btn

    def set_workspace(self, workspace) -> None:
        self._workspace = workspace

    def setContent(self, widget: QWidget) -> None:
        if self._content is widget:
            return
        if self._content:
            self._content.setParent(None)
        self._content = widget
        self.content_layout.addWidget(widget)
        widget.show()
        self.content_area.setMaximumHeight(widget.sizeHint().height() + 40)

    def setTitle(self, text: str) -> None:
        self.title_label.setText(text)

    def set_status(self, color: str) -> None:
        self._status_color = color
        self.status_light.setStyleSheet(f"background: {color}; border-radius: 7px;")

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self.setProperty("state", "collapsed" if self._collapsed else "default")
        end_value = 0 if self._collapsed else max(120, self.content_area.sizeHint().height())
        self._animate_collapse(end_value)

    def toggle_hide(self) -> None:
        self._hidden = not self._hidden
        if self._hidden:
            self._animate_collapse(0)
            self.btn_hide.setText("⇥")
        else:
            self._animate_collapse(max(120, self.content_area.sizeHint().height()))
            self.btn_hide.setText("⤬")

    def toggle_maximize(self) -> None:
        if self._workspace:
            self._workspace.toggle_maximize(self)

    def toggle_detach(self) -> None:
        if self._floating_window:
            self._reattach_content()
            return
        if not self._content:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.title_label.text())
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self._content)
        self._floating_window = dlg
        dlg.finished.connect(self._reattach_content)
        dlg.resize(720, 520)
        dlg.show()

    def _reattach_content(self) -> None:
        if self._floating_window and self._content:
            self._content.setParent(self.content_area)
            self.content_layout.addWidget(self._content)
            self._floating_window = None

    def _animate_collapse(self, end_value: int) -> None:
        start_value = self.content_area.maximumHeight()
        self._collapse_anim.stop()
        self._collapse_anim.setStartValue(start_value)
        self._collapse_anim.setEndValue(end_value)
        self._collapse_anim.start()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)

    def set_maximized_state(self, maximized: bool) -> None:
        self.setProperty("state", "maximized" if maximized else "default")
        self.style().unpolish(self)
        self.style().polish(self)


class PanelWorkspacePage(QWidget):
    """Grid-based layout for arranging PanelWindow instances."""

    def __init__(self, columns: int = 2, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.columns = max(1, columns)
        self.panels: List[PanelWindow] = []
        self._maximized_panel: Optional[PanelWindow] = None
        self._next_row = 0
        self._next_col = 0

        self.grid = QGridLayout(self)
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(12, 12, 12, 12)

    def add_panel(self, panel: PanelWindow, column_span: int = 1) -> PanelWindow:
        span = max(1, min(column_span, self.columns))
        if self._next_col + span > self.columns:
            self._next_row += 1
            self._next_col = 0
        row = self._next_row
        col = self._next_col
        self._next_col += span
        if self._next_col >= self.columns:
            self._next_row += 1
            self._next_col = 0
        self.grid.addWidget(panel, row, col, 1, span)
        panel.set_workspace(self)
        self.panels.append(panel)
        return panel

    def toggle_maximize(self, panel: PanelWindow) -> None:
        if self._maximized_panel is panel:
            self._restore_panels()
            return
        self._maximized_panel = panel
        for p in self.panels:
            if p is panel:
                p.show()
                p.set_maximized_state(True)
            else:
                p.hide()

    def _restore_panels(self) -> None:
        for p in self.panels:
            p.show()
            p.set_maximized_state(False)
        self._maximized_panel = None
