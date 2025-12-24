"""
Shared theme utilities for the NetReaper GUIs.

Provides a single place to load and apply the cyber/biotech inspired QSS so
both the Linux and Windows interfaces stay visually consistent.
"""

from PyQt6.QtWidgets import QApplication

BIO_LAB_QSS = r"""
QWidget {
    background-color: #06090f;
    color: #e6f1ff;
    font-family: "Agency FB", "Consolas", "Courier New", monospace;
    font-size: 12px;
}
QLabel {
    color: #e6f1ff;
}
QGroupBox {
    border: 1px solid rgba(120,180,255,0.35);
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0b1220, stop:1 #0a0f1a);
    font-weight: bold;
    color: #e6f1ff;
}
QGroupBox::title {
    color: #5ad6ff;
    padding: 4px 6px 0 6px;
    font-size: 13px;
    text-transform: uppercase;
}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTreeWidget, QTextEdit {
    background: #0b1220;
    border: 1px solid rgba(120,180,255,0.35);
    border-radius: 6px;
    padding: 6px;
    selection-background-color: rgba(90, 214, 255, 0.25);
}
QPlainTextEdit#outputLog {
    background: #05070d;
    color: #9ef8c9;
    font-family: "Courier New", monospace;
}
QLineEdit#commandInput {
    background: #0f1a2d;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(120,180,255,0.35),
        stop:1 rgba(0,0,0,0.4));
    border: 1px solid rgba(120,180,255,0.45);
    border-radius: 6px;
    padding: 7px 14px;
    color: #e6f1ff;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    border-color: rgba(90, 214, 255, 0.75);
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(120,180,255,0.55),
        stop:1 rgba(0,0,0,0.45));
}
QPushButton:pressed {
    background: rgba(0,0,0,0.65);
}
QPushButton[panelButton="true"] {
    padding: 4px 8px;
    min-width: 20px;
}
QListWidget#navList {
    background: #05070d;
    border: 1px solid rgba(120,180,255,0.30);
    border-radius: 10px;
}
QListWidget#navList::item {
    padding: 10px 8px;
    margin: 2px;
}
QListWidget#navList::item:selected {
    background: rgba(90, 214, 255, 0.18);
    border-left: 3px solid #5ad6ff;
}
#panelWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f1727, stop:1 #0a0f1a);
    border: 1px solid rgba(120,180,255,0.35);
    border-radius: 12px;
    padding: 6px;
}
#panelWindow[state="maximized"] {
    border-color: rgba(0, 255, 156, 0.85);
}
#panelWindow[state="collapsed"] {
    border-color: rgba(120,180,255,0.15);
    background: #0a0f1a;
}
#panelHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0c1422, stop:1 #0d1c2f);
    border-radius: 9px;
    padding: 6px 10px;
    border: 1px solid rgba(120,180,255,0.25);
}
#statusLight {
    width: 12px;
    height: 12px;
    border-radius: 6px;
    background: #3dd598;
    border: 1px solid rgba(0,0,0,0.45);
}
QSplitter::handle {
    background: rgba(120,180,255,0.25);
}
QScrollArea {
    border: none;
    background: transparent;
}
QToolBar {
    background: #0a101b;
    border: 1px solid rgba(120,180,255,0.25);
}
"""


def apply_bio_theme(app: QApplication) -> None:
    """Apply the shared NetReaper QSS theme to the given QApplication."""
    app.setStyleSheet(BIO_LAB_QSS)
