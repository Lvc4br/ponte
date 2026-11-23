import sys

from PySide6.QtWidgets import QApplication

from app.ui.ponte_shell import PonteMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PONTE")
    app.setOrganizationName("EGT Engenharia")
    window = PonteMainWindow()
    window.show()
    return app.exec()
