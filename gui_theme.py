"""
Shared theme utilities for the NetReaper GUIs.

Provides a single place to load and apply the cyber/biotech inspired QSS so
both the Linux and Windows interfaces stay visually consistent.
"""

from PyQt6.QtWidgets import QApplication

BIO_LAB_QSS = r"""
/*
NET-NiNJA "Command Center" theme.

Design intent: match the provided NET-NiNJA reference UI as closely as Qt/QSS
allows without shipping a full custom scene-graph renderer.

Rules:
- Pure-black base background.
- Crisp neon outlines (no blurry glow in hit-areas).
- Module navigation buttons have distinct neon accents.
*/

QWidget {
    background-color: #000000;
    color: #d7e6ff;
    font-family: "Agency FB", "Rajdhani", "Consolas", "Courier New", monospace;
    font-size: 12px;
}
QLabel {
    color: rgba(210,230,255,0.85);
}

/* ────────────────────────────────────────────────────────────────
   Header (NET-NiNJA hero strip)
   ──────────────────────────────────────────────────────────────── */
#reaperHeader {
    background: transparent;
    border: none;
}
#headerRule {
    background: rgba(255,255,255,0.06);
    height: 1px;
}
#reaperStats {
    background: transparent;
}
#headerMeta {
    color: rgba(210,230,255,0.65);
    font-size: 12px;
}
#headerMetaStrong {
    color: rgba(210,230,255,0.85);
    font-weight: 700;
}
QGroupBox {
    border: 1px solid rgba(0,255,0,0.30);
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px;
    background: rgba(0,0,0,0.35);
    font-weight: bold;
    color: #e6f1ff;
}
QGroupBox::title {
    color: rgba(0,255,0,0.75);
    padding: 4px 6px 0 6px;
    font-size: 13px;
    text-transform: uppercase;
}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTreeWidget, QTextEdit {
    background: rgba(0,0,0,0.55);
    border: 1px solid rgba(0,255,0,0.22);
    border-radius: 6px;
    padding: 6px;
    selection-background-color: rgba(90, 214, 255, 0.25);
}
QPlainTextEdit#outputLog {
    background: rgba(0,0,0,0.65);
    color: rgba(0,255,128,0.75);
    font-family: "Courier New", monospace;
}
QLineEdit#commandInput {
    background: #0f1a2d;
}
QPushButton {
    background: rgba(0,0,0,0.55);
    border: 1px solid rgba(120,180,255,0.35);
    border-radius: 6px;
    padding: 7px 14px;
    color: #e6f1ff;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    border-color: rgba(0,255,255,0.75);
    background: rgba(0,0,0,0.65);
}
QPushButton:pressed {
    background: rgba(0,0,0,0.65);
}

/* Camera tab action buttons: force readable labels on all platforms. */
QPushButton[camAction="true"] {
    color: #e6f1ff;
    font-weight: 700;
}


/* Left-side quick actions: gray pills like reference. */
QPushButton[quickAction="true"] {
    background: rgba(20,20,20,0.85);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 8px;
    color: rgba(230,240,255,0.80);
    padding: 10px 14px;
}
QPushButton[quickAction="true"]:hover {
    border-color: rgba(255,255,255,0.35);
}

/* Module navigation buttons (the neon strip buttons). */
QPushButton[navRole="scan"]    { border: 2px solid rgba(0,255,0,0.80);    color: rgba(0,255,0,0.85); }
QPushButton[navRole="recon"]   { border: 2px solid rgba(0,200,255,0.80);  color: rgba(0,200,255,0.85); }
QPushButton[navRole="wireless"]{ border: 2px solid rgba(255,120,0,0.85);  color: rgba(255,140,50,0.90); }
QPushButton[navRole="web"]     { border: 2px solid rgba(255,0,180,0.85);  color: rgba(255,80,210,0.90); }
QPushButton[navRole="cameras"] { border: 2px solid rgba(90,214,255,0.80); color: rgba(90,214,255,0.85); }
QPushButton[navRole="tools"]   { border: 2px solid rgba(255,200,0,0.85);  color: rgba(255,220,80,0.95); }
QPushButton[navRole="wizards"] { border: 2px solid rgba(160,80,255,0.85); color: rgba(190,130,255,0.95); }
QPushButton[navRole="jobs"]    { border: 2px solid rgba(0,255,200,0.85);  color: rgba(80,255,220,0.95); }
QPushButton[navRole] {
    background: rgba(0,0,0,0.50);
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 14px;
    font-weight: 700;
}
QPushButton[navRole]:hover {
    background: rgba(0,0,0,0.70);
}
QPushButton[panelButton="true"] {
    padding: 4px 8px;
    min-width: 20px;
}
QListWidget#navList {
    background: rgba(0,0,0,0.55);
    border: 1px solid rgba(255,255,255,0.12);
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
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(0,255,0,0.22);
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
    background: rgba(0,0,0,0.65);
    border-radius: 9px;
    padding: 6px 10px;
    border: 1px solid rgba(255,255,255,0.12);
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
    background: rgba(0,0,0,0.55);
    border: none;
}

QMenuBar {
    background: rgba(0,0,0,0.55);
    border: none;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
}
QMenuBar::item:selected {
    background: rgba(255,255,255,0.10);
}
"""


def apply_bio_theme(app: QApplication) -> None:
    """Apply the shared NetReaper QSS theme to the given QApplication."""
    app.setStyleSheet(BIO_LAB_QSS)
