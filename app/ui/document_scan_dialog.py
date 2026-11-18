import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QSplitter, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)


class DocumentScanDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PONTE | Resultado da análise documental")
        self.resize(1050, 680)
        layout = QVBoxLayout(self)
        summary = QLabel(self._summary(results))
        summary.setWordWrap(True)
        layout.addWidget(summary)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Arquivo e conteúdo extraído"])
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Selecione um arquivo ou seção para visualizar o conteúdo.")
        splitter.addWidget(self.tree)
        splitter.addWidget(self.preview)
        splitter.setSizes([360, 690])
        layout.addWidget(splitter, 1)

        for result in results:
            label = f"{result.file_name} — {result.status}"
            root = QTreeWidgetItem([label])
            root.setData(0, Qt.ItemDataRole.UserRole, {
                "metadata": result.metadata,
                "warnings": result.warnings,
                "errors": result.errors,
                "sha256": result.sha256,
                "path": result.path,
            })
            self.tree.addTopLevelItem(root)
            for section in result.sections:
                child = QTreeWidgetItem([f"{section.locator} — {section.kind}"])
                child.setData(0, Qt.ItemDataRole.UserRole, section.content)
                root.addChild(child)
            root.setExpanded(False)
        self.tree.currentItemChanged.connect(self._show_item)
        self.tree.expandToDepth(0)

    @staticmethod
    def _summary(results):
        counts = {}
        for result in results:
            counts[result.status] = counts.get(result.status, 0) + 1
        detail = " · ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
        return f"Arquivos analisados: {len(results)}    |    {detail}"

    def _show_item(self, current, _previous):
        if current is None:
            self.preview.clear()
            return
        value = current.data(0, Qt.ItemDataRole.UserRole)
        self.preview.setPlainText(json.dumps(value, ensure_ascii=False, indent=2, default=str))
