import sys

from PySide6.QtWidgets import QApplication

from app.ui.engineering_workspace import EngineeringWorkspaceWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gerenciador de Estruturas")
    window = EngineeringWorkspaceWindow()
    window.show()
    return app.exec()
