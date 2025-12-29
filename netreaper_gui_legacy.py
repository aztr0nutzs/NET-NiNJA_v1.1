# ================================
# NET-NiNJA LEGACY ENTRYPOINT
# ================================

import os

# ---- HARD LEGACY LOCKDOWN (MUST BE FIRST) ----
os.environ["QT_OPENGL"] = "software"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_MEDIA_BACKEND"] = "software"
os.environ["QT_LOGGING_RULES"] = "*.debug=false"

# ---- CPU FEATURE CHECK ----
from cpu_features import is_legacy_cpu

LEGACY_MODE = True

if not is_legacy_cpu():
    # Safety: even if CPU claims modern features, allow override
    LEGACY_MODE = False

# ---- NOW SAFE TO IMPORT QT ----
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# ---- IMPORT MAIN GUI ----
import netreaper_gui


def main():
    app = QApplication(sys.argv)

    # ---- LEGACY GUI STABILITY SETTINGS ----
    app.setEffectEnabled(Qt.UI_AnimateMenu, False)
    app.setEffectEnabled(Qt.UI_AnimateTooltip, False)
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)

    QApplication.setFont(QFont("Arial", 9))

    # ---- INFORM CORE GUI ----
    netreaper_gui.LEGACY_MODE = True

    gui = netreaper_gui.NetReaperGui()
    gui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
