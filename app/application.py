import sys

from PySide6.QtWidgets import QApplication

from app.ui.spreadsheet_window import SpreadsheetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PONTE")
    window = SpreadsheetWindow()
    window.show()
    return app.exec()
