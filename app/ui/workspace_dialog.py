"""Basic desktop workspace for generic projects and editable data tables."""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.workspace.exchange import SpreadsheetExchange


class WorkspaceDialog(QDialog):
    def __init__(self, store, document_index=None, parent=None):
        super().__init__(parent)
        self.store = store
        self.document_index = document_index
        self.exchange = SpreadsheetExchange(store)
        self.project_id = None
        self.table_id = None
        self.columns = []
        self._loading = False
        self.setWindowTitle("PONTE | Espaço de dados")
        self.resize(1150, 720)

        root = QVBoxLayout(self)
        project_row = QHBoxLayout()
        project_row.addWidget(QLabel("Projeto"))
        self.projects = QComboBox()
        self.projects.currentIndexChanged.connect(self._project_changed)
        project_row.addWidget(self.projects, 1)
        self.add_project_button = QPushButton("Novo projeto")
        self.add_project_button.clicked.connect(self._add_project)
        project_row.addWidget(self.add_project_button)
        rename_project = QPushButton("Renomear")
        rename_project.clicked.connect(self._rename_project)
        project_row.addWidget(rename_project)
        delete_project = QPushButton("Excluir projeto")
        delete_project.clicked.connect(self._delete_project)
        project_row.addWidget(delete_project)
        root.addLayout(project_row)

        table_row = QHBoxLayout()
        table_row.addWidget(QLabel("Tabela"))
        self.tables = QComboBox()
        self.tables.currentIndexChanged.connect(self._table_changed)
        table_row.addWidget(self.tables, 1)
        action_row = QHBoxLayout()
        actions = (
            ("Nova tabela", self._add_table),
            ("Renomear tabela", self._rename_table),
            ("Excluir tabela", self._delete_table),
            ("Nova coluna", self._add_column),
            ("Coluna calculada", self._add_formula_column),
            ("Excluir coluna", self._delete_column),
            ("Novo registro", self._add_record),
            ("Excluir registro", self._delete_record),
            ("Importar CSV", self._import_csv),
            ("Importar Excel", self._import_xlsx),
            ("Exportar CSV", self._export_csv),
            ("Exportar Excel", self._export_xlsx),
            ("Vincular documento", self._link_document),
            ("Documentos do projeto", self._show_project_documents),
        )
        for index, (label, callback) in enumerate(actions):
            button = QPushButton(label)
            button.clicked.connect(callback)
            (table_row if index < 7 else action_row).addWidget(button)
        root.addLayout(table_row)
        root.addLayout(action_row)

        self.grid = QTableWidget()
        self.grid.setAlternatingRowColors(True)
        self.grid.setSortingEnabled(False)
        self.grid.cellChanged.connect(self._cell_changed)
        root.addWidget(self.grid, 1)
        self.status = QLabel("Os dados são armazenados localmente no SQLite.")
        root.addWidget(self.status)
        self._refresh_projects()

    def _refresh_projects(self, select_id=None):
        self.projects.blockSignals(True)
        self.projects.clear()
        for project in self.store.list_projects():
            self.projects.addItem(project["name"], project["id"])
        if select_id is not None:
            index = self.projects.findData(select_id)
            if index >= 0:
                self.projects.setCurrentIndex(index)
        self.projects.blockSignals(False)
        if self.projects.count() == 0:
            self.project_id = self.store.create_project("Meu espaço de dados")
            self._refresh_projects(self.project_id)
        else:
            self._project_changed(self.projects.currentIndex())

    def _project_changed(self, index):
        if index < 0:
            return
        self.project_id = self.projects.currentData()
        self.tables.blockSignals(True)
        self.tables.clear()
        for table in self.store.list_tables(self.project_id):
            self.tables.addItem(table["name"], table["id"])
        self.tables.blockSignals(False)
        if self.tables.count():
            self.tables.setCurrentIndex(0)
            self._table_changed(0)
        else:
            self.table_id = None
            self.columns = []
            self.grid.clear()
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)

    def _table_changed(self, index):
        if index < 0:
            self.table_id = None
            self.columns = []
            self.grid.clear()
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            return
        self.table_id = self.tables.currentData()
        self._refresh_grid()

    def _refresh_grid(self):
        if self.table_id is None:
            return
        self.columns = self.store.list_columns(self.table_id)
        records = self.store.list_records(self.table_id)
        self._loading = True
        self.grid.clear()
        self.grid.setColumnCount(len(self.columns) + 1)
        self.grid.setHorizontalHeaderLabels(["ID"] + [
            f"{column['name']} · {column['data_type']}" for column in self.columns
        ])
        self.grid.setColumnHidden(0, True)
        self.grid.setRowCount(len(records))
        for row_index, record in enumerate(records):
            id_item = QTableWidgetItem(str(record["id"]))
            id_item.setData(Qt.ItemDataRole.UserRole, record["id"])
            self.grid.setItem(row_index, 0, id_item)
            for column_index, column in enumerate(self.columns, start=1):
                value = record["values"].get(column["name"])
                item = QTableWidgetItem("" if value is None else str(value))
                item.setData(Qt.ItemDataRole.UserRole, column["name"])
                if column.get("formula"):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(f"Fórmula: {column['formula']}")
                self.grid.setItem(row_index, column_index, item)
        self._loading = False
        self.status.setText(
            f"{len(records)} registro(s) · {len(self.columns)} coluna(s) · armazenamento local"
        )

    def _add_project(self):
        name, ok = QInputDialog.getText(self, "Novo projeto", "Nome do projeto:")
        if not ok:
            return
        try:
            project_id = self.store.create_project(name)
            self._refresh_projects(project_id)
        except Exception as exc:
            QMessageBox.warning(self, "Projeto", str(exc))

    def _add_table(self):
        if self.project_id is None:
            return
        name, ok = QInputDialog.getText(self, "Nova tabela", "Nome da tabela:")
        if not ok:
            return
        try:
            table_id = self.store.create_table(self.project_id, name)
            self._project_changed(self.projects.currentIndex())
            index = self.tables.findData(table_id)
            if index >= 0:
                self.tables.setCurrentIndex(index)
        except Exception as exc:
            QMessageBox.warning(self, "Tabela", str(exc))

    def _rename_project(self):
        if self.project_id is None:
            return
        current = self.projects.currentText()
        name, ok = QInputDialog.getText(self, "Renomear projeto", "Nome:", text=current)
        if ok:
            try:
                self.store.update_project(self.project_id, name=name)
                self._refresh_projects(self.project_id)
            except Exception as exc:
                QMessageBox.warning(self, "Projeto", str(exc))

    def _delete_project(self):
        if self.project_id is None:
            return
        if QMessageBox.question(
            self, "Excluir projeto",
            "Isso excluirá as tabelas e registros deste projeto. Deseja continuar?"
        ) != QMessageBox.StandardButton.Yes:
            return
        self.store.delete_project(self.project_id)
        self._refresh_projects()

    def _rename_table(self):
        if self.table_id is None:
            return
        name, ok = QInputDialog.getText(
            self, "Renomear tabela", "Nome:", text=self.tables.currentText()
        )
        if ok:
            try:
                self.store.update_table(self.table_id, name=name)
                self._project_changed(self.projects.currentIndex())
            except Exception as exc:
                QMessageBox.warning(self, "Tabela", str(exc))

    def _delete_table(self):
        if self.table_id is None:
            return
        if QMessageBox.question(
            self, "Excluir tabela",
            "A tabela e seus registros serão excluídos. Deseja continuar?"
        ) != QMessageBox.StandardButton.Yes:
            return
        self.store.delete_table(self.table_id)
        self._project_changed(self.projects.currentIndex())

    def _delete_column(self):
        if self.table_id is None or not self.columns:
            return
        names = [column["name"] for column in self.columns]
        name, ok = QInputDialog.getItem(self, "Excluir coluna", "Coluna:", names, 0, False)
        if not ok:
            return
        column = next(item for item in self.columns if item["name"] == name)
        if QMessageBox.question(
            self, "Excluir coluna",
            f"Remover '{name}' e os valores dessa coluna em todos os registros?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.delete_column(column["id"])
            self._refresh_grid()
        except Exception as exc:
            QMessageBox.warning(self, "Coluna", str(exc))

    def _add_column(self):
        if self.table_id is None:
            QMessageBox.information(self, "Coluna", "Crie ou selecione uma tabela primeiro.")
            return
        name, ok = QInputDialog.getText(self, "Nova coluna", "Nome da coluna:")
        if not ok:
            return
        data_type, ok = QInputDialog.getItem(
            self, "Tipo da coluna", "Tipo:", 
            ["text", "integer", "decimal", "boolean", "date", "datetime", "json"], 0, False
        )
        if not ok:
            return
        try:
            self.store.add_column(self.table_id, name, data_type)
            self._refresh_grid()
        except Exception as exc:
            QMessageBox.warning(self, "Coluna", str(exc))

    def _add_formula_column(self):
        if self.table_id is None:
            QMessageBox.information(self, "Fórmula", "Selecione uma tabela primeiro.")
            return
        name, ok = QInputDialog.getText(self, "Coluna calculada", "Nome da coluna:")
        if not ok:
            return
        formula, ok = QInputDialog.getText(
            self, "Fórmula", "Expressão (ex.: [Quantidade] * [Preço unitário]):"
        )
        if not ok:
            return
        data_type, ok = QInputDialog.getItem(
            self, "Tipo do resultado", "Tipo:",
            ["decimal", "integer", "text", "boolean", "date", "datetime", "json"], 0, False
        )
        if not ok:
            return
        try:
            self.store.add_column(self.table_id, name, data_type, formula=formula)
            self._refresh_grid()
        except Exception as exc:
            QMessageBox.warning(self, "Fórmula inválida", str(exc))

    def _add_record(self):
        if self.table_id is None or not self.columns:
            QMessageBox.information(self, "Registro", "Crie uma tabela e ao menos uma coluna.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo registro")
        dialog.resize(520, min(760, 160 + 58 * len(self.columns)))
        outer = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        controls = {}
        for column in self.columns:
            if column.get("formula"):
                continue
            data_type = column["data_type"]
            default = column["default"]
            if data_type == "boolean":
                control = QCheckBox()
                control.setChecked(bool(default) if default is not None else False)
            elif data_type == "json":
                control = QPlainTextEdit()
                control.setMaximumHeight(90)
                control.setPlainText(
                    json.dumps(default, ensure_ascii=False, indent=2)
                    if default is not None else ""
                )
            else:
                control = QLineEdit()
                control.setPlaceholderText(
                    "" if default is None else f"Padrão: {default}"
                )
                if default is not None:
                    control.setText(str(default))
            form.addRow(f"{column['name']} ({data_type})", control)
            controls[column["name"]] = control
        scroll.setWidget(form_widget)
        outer.addWidget(scroll, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        outer.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            values = {}
            for column in self.columns:
                name = column["name"]
                if column.get("formula"):
                    continue
                control = controls[name]
                if column["data_type"] == "boolean":
                    value = control.isChecked()
                elif column["data_type"] == "json":
                    raw = control.toPlainText().strip()
                    value = None if not raw else json.loads(raw)
                else:
                    raw = control.text().strip()
                    value = self._parse_cell(raw, column["data_type"])
                    if value is None and column["default"] is not None:
                        value = column["default"]
                values[name] = value
            self.store.insert_record(self.table_id, values)
            self._refresh_grid()
        except Exception as exc:
            QMessageBox.warning(self, "Registro inválido", str(exc))

    def _parse_cell(self, raw, data_type):
        if raw == "":
            return None
        if data_type == "text":
            return raw
        if data_type == "integer":
            return int(raw)
        if data_type == "decimal":
            return float(raw.replace(",", "."))
        if data_type == "boolean":
            value = raw.strip().casefold()
            if value in {"true", "1", "sim", "yes"}:
                return True
            if value in {"false", "0", "não", "nao", "no"}:
                return False
            raise ValueError("Use verdadeiro/falso ou sim/não.")
        if data_type in {"json"}:
            return json.loads(raw)
        return raw

    def _cell_changed(self, row, column_index):
        if self._loading or column_index == 0 or self.table_id is None:
            return
        try:
            record_id = self.grid.item(row, 0).data(Qt.ItemDataRole.UserRole)
            column = self.columns[column_index - 1]
            raw = self.grid.item(row, column_index).text()
            value = self._parse_cell(raw, column["data_type"])
            self.store.update_record(record_id, {column["name"]: value})
            self.status.setText("Registro atualizado.")
        except Exception as exc:
            QMessageBox.warning(self, "Valor inválido", str(exc))
            self._refresh_grid()

    def _delete_record(self):
        row = self.grid.currentRow()
        if row < 0:
            return
        record_id = self.grid.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Excluir registro", "Deseja excluir o registro selecionado?") != QMessageBox.StandardButton.Yes:
            return
        self.store.delete_record(record_id)
        self._refresh_grid()

    def _import_csv(self):
        if self.project_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Importar CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            preview = self.exchange.preview_csv(path, limit=5)
            sample = "\n".join(" | ".join(str(value) for value in row) for row in preview["rows"])
            answer = QMessageBox.question(
                self, "Prévia do CSV",
                f"Arquivo: {preview['file_name']}\nSeparador: {preview['delimiter']!r}\n\n"
                f"{sample}\n\nImportar este conteúdo como uma nova tabela?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            table_id = self.exchange.import_csv(self.project_id, path)
            self._project_changed(self.projects.currentIndex())
            self.tables.setCurrentIndex(self.tables.findData(table_id))
        except Exception as exc:
            QMessageBox.warning(self, "Importação CSV", str(exc))

    def _import_xlsx(self):
        if self.project_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Importar Excel", "", "Excel (*.xlsx *.xlsm)")
        if not path:
            return
        try:
            preview = self.exchange.preview_xlsx(path, limit=4)
            summary = []
            for sheet in preview["sheets"]:
                rows = "\n".join(
                    " | ".join(str(value) for value in row)
                    for row in sheet["rows"]
                )
                summary.append(f"Aba: {sheet['sheet_name']}\n{rows}")
            answer = QMessageBox.question(
                self, "Prévia do Excel",
                f"Arquivo: {preview['file_name']}\n\n" +
                "\n\n".join(summary) +
                "\n\nImportar todas as abas como tabelas deste projeto?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            table_ids = self.exchange.import_xlsx(self.project_id, path)
            self._project_changed(self.projects.currentIndex())
            if table_ids:
                self.tables.setCurrentIndex(self.tables.findData(table_ids[0]))
        except Exception as exc:
            QMessageBox.warning(self, "Importação Excel", str(exc))

    def _link_document(self):
        if self.project_id is None or self.document_index is None:
            return
        documents = self.document_index.list_documents()
        if not documents:
            QMessageBox.information(
                self, "Documentos", "Analise ao menos um documento antes de vinculá-lo."
            )
            return
        labels = [
            f"{item['file_name']} · {item['status']} · ID {item['id']}"
            for item in documents
        ]
        label, ok = QInputDialog.getItem(
            self, "Vincular documento", "Documento analisado:", labels, 0, False
        )
        if not ok:
            return
        document = documents[labels.index(label)]
        try:
            self.store.link_document(self.project_id, document["id"])
            self.status.setText(f"Documento vinculado: {document['file_name']}")
        except Exception as exc:
            QMessageBox.warning(self, "Vincular documento", str(exc))

    def _show_project_documents(self):
        if self.project_id is None:
            return
        documents = self.store.list_project_documents(self.project_id)
        if not documents:
            QMessageBox.information(self, "Documentos do projeto", "Nenhum documento vinculado.")
            return
        lines = [
            f"{item['file_name']} · {item['extension']} · {item['status']} · {item['scanned_at']}"
            for item in documents
        ]
        QMessageBox.information(self, "Documentos do projeto", "\n".join(lines))

    def _export_csv(self):
        if self.table_id is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "", "CSV (*.csv)")
        if path:
            try:
                self.exchange.export_csv(self.table_id, path)
            except Exception as exc:
                QMessageBox.warning(self, "Exportação CSV", str(exc))

    def _export_xlsx(self):
        if self.table_id is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Excel", "", "Excel (*.xlsx)")
        if path:
            try:
                self.exchange.export_xlsx(self.table_id, path)
            except Exception as exc:
                QMessageBox.warning(self, "Exportação Excel", str(exc))
