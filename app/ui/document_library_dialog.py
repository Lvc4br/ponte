import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout,
)


class DocumentLibraryDialog(QDialog):
    def __init__(self, document_index, parent=None):
        super().__init__(parent)
        self.document_index = document_index
        self.setWindowTitle("PONTE | Biblioteca documental")
        self.resize(1050, 680)
        layout = QVBoxLayout(self)
        documents = document_index.list_documents()
        layout.addWidget(QLabel(f"Documentos registrados localmente: {len(documents)}"))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Documento e conteúdo"])
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.preview)
        splitter.setSizes([360, 690])
        layout.addWidget(splitter, 1)

        for document in documents:
            root = QTreeWidgetItem([
                f"{document['file_name']} — {document['status']} — "
                f"{document['section_count']} seção(ões)"
            ])
            root.setData(0, Qt.ItemDataRole.UserRole, document["id"])
            self.tree.addTopLevelItem(root)
            stored = document_index.get_document(document["id"])
            for section in stored["sections"]:
                child = QTreeWidgetItem([
                    f"{section['locator']} — {section['kind']}"
                ])
                child.setData(0, Qt.ItemDataRole.UserRole, section["content"])
                root.addChild(child)
            root.setExpanded(False)
        self.tree.currentItemChanged.connect(self._show_item)
        self.tree.expandToDepth(0)

    def _show_item(self, current, _previous):
        if current is None:
            self.preview.clear()
            return
        value = current.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(value, int):
            value = self.document_index.get_document(value)
        self.preview.setPlainText(
            json.dumps(value, ensure_ascii=False, indent=2, default=str)
        )
