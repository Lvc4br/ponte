"""Basic desktop workspace for generic projects and editable data tables."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
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
        self.resize(1320, 820)


        self.setMinimumSize(980, 650)
        self.setStyleSheet("""
            QDialog { background: #171c24; color: #e8edf4; }
            QLabel { color: #e3e9f1; }
            QLabel#eyebrow { color: #e6a04b; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
            QLabel#muted { color: #9aa8b8; }
            QFrame#header, QGroupBox { background: #202936; border: 1px solid #344254; border-radius: 8px; }
            QGroupBox { margin-top: 10px; padding: 12px 8px 8px 8px; font-weight: 700; color: #dce5ef; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QComboBox, QLineEdit, QPlainTextEdit { background: #151d28; color: #edf2f8; border: 1px solid #405168; border-radius: 6px; padding: 8px; min-height: 20px; }
            QComboBox:focus, QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #d9903e; }
            QPushButton { background: #2d3b4c; color: #edf2f8; border: 1px solid #43566d; border-radius: 6px; padding: 8px 12px; min-height: 20px; }
            QPushButton:hover { background: #3a4b60; border-color: #d9903e; }
            QPushButton#primary { background: #b97532; border-color: #d9903e; color: white; font-weight: 700; }
            QPushButton#primary:hover { background: #cb8740; }
            QTabWidget::pane { border: 1px solid #344254; border-radius: 7px; background: #1c2531; top: -1px; }
            QTabBar::tab { background: #263343; color: #aebccc; padding: 10px 18px; margin-right: 3px; border: 1px solid #344254; border-bottom: 0; }
            QTabBar::tab:selected { background: #1c2531; color: #f0b15f; border-top: 2px solid #df9848; }
            QTableWidget { background: #18212c; alternate-background-color: #202c39; color: #e5ebf2; gridline-color: #344254; border: 1px solid #344254; selection-background-color: #654a2f; selection-color: white; }
            QHeaderView::section { background: #2c3b4d; color: #e8edf4; padding: 9px; border: 0; border-right: 1px solid #405168; border-bottom: 1px solid #405168; font-weight: 700; }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(11)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        identity = QVBoxLayout()
        title = QLabel("PONTE  /  ESPAÇO DE TRABALHO")
        title.setObjectName("eyebrow")
        identity.addWidget(title)
        subtitle = QLabel("Organize dados, tabelas e documentos em um único projeto.")
        subtitle.setObjectName("muted")
        identity.addWidget(subtitle)
        header_layout.addLayout(identity, 1)
        project_controls = QVBoxLayout()
        project_label = QLabel("PROJETO ATUAL")
        project_label.setObjectName("eyebrow")
        project_controls.addWidget(project_label)
        self.projects = QComboBox()
        self.projects.setMinimumWidth(210)
        self.projects.currentIndexChanged.connect(self._project_changed)
        project_controls.addWidget(self.projects)
        header_layout.addLayout(project_controls)
        self.add_project_button = QPushButton("＋ Novo projeto")
        self.add_project_button.setObjectName("primary")
        self.add_project_button.clicked.connect(self._add_project)
        header_layout.addWidget(self.add_project_button)
        rename_project = QPushButton("Renomear")
        rename_project.clicked.connect(self._rename_project)
        header_layout.addWidget(rename_project)
        delete_project = QPushButton("Excluir")
        delete_project.clicked.connect(self._delete_project)
        header_layout.addWidget(delete_project)
        root.addWidget(header)

        table_group = QGroupBox("TABELA ATUAL")
        table_row = QHBoxLayout(table_group)
        self.tables = QComboBox()
        self.tables.setMinimumWidth(230)
        self.tables.currentIndexChanged.connect(self._table_changed)
        table_row.addWidget(self.tables, 1)
        for label, callback in (("＋ Nova tabela", self._add_table), ("Renomear", self._rename_table), ("Excluir", self._delete_table)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            table_row.addWidget(button)
        root.addWidget(table_group)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        groups = [
            ("ESTRUTURA", [("＋ Coluna", self._add_column), ("ƒ Coluna calculada", self._add_formula_column), ("Excluir coluna", self._delete_column)]),
            ("REGISTROS", [("＋ Registro", self._add_record), ("Excluir registro", self._delete_record)]),
            ("INTERCÂMBIO", [("Importar CSV", self._import_csv), ("Importar Excel", self._import_xlsx), ("Exportar CSV", self._export_csv), ("Exportar Excel", self._export_xlsx)]),
        ]
        for group_title, actions in groups:
            group = QGroupBox(group_title)
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(8, 10, 8, 7)
            group_layout.setSpacing(5)
            for label, callback in actions:
                button = QPushButton(label)
                button.clicked.connect(callback)
                group_layout.addWidget(button)
            toolbar.addWidget(group, 1)
        root.addLayout(toolbar)

        self.tabs = QTabWidget()
        data_page = QWidget()
        data_layout = QVBoxLayout(data_page)
        data_layout.setContentsMargins(10, 10, 10, 10)
        data_heading = QHBoxLayout()
        data_title = QLabel("DADOS DA TABELA")
        data_title.setObjectName("eyebrow")
        data_heading.addWidget(data_title)
        data_heading.addStretch()
        self.grid_count = QLabel("Selecione uma tabela")
        self.grid_count.setObjectName("muted")
        data_heading.addWidget(self.grid_count)
        data_layout.addLayout(data_heading)
        self.grid = QTableWidget()
        self.grid.setAlternatingRowColors(True)
        self.grid.setSortingEnabled(True)
        self.grid.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.grid.setWordWrap(False)
        self.grid.verticalHeader().setDefaultSectionSize(34)
        self.grid.verticalHeader().setVisible(True)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.grid.horizontalHeader().setDefaultSectionSize(150)
        self.grid.horizontalHeader().setMinimumSectionSize(90)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.cellChanged.connect(self._cell_changed)
        data_layout.addWidget(self.grid, 1)
        self.tabs.addTab(data_page, "▦  Dados")

        documents_page = QWidget()
        documents_layout = QVBoxLayout(documents_page)
        documents_layout.setContentsMargins(12, 12, 12, 12)
        documents_header = QHBoxLayout()
        documents_intro = QVBoxLayout()
        documents_title = QLabel("DOCUMENTOS DO PROJETO")
        documents_title.setObjectName("eyebrow")
        documents_intro.addWidget(documents_title)
        documents_hint = QLabel("Consulte os arquivos analisados e vinculados ao projeto selecionado.")
        documents_hint.setObjectName("muted")
        documents_hint.setWordWrap(True)
        documents_intro.addWidget(documents_hint)
        documents_header.addLayout(documents_intro, 1)
        link_button = QPushButton("＋ Vincular documento")
        link_button.setObjectName("primary")
        link_button.clicked.connect(self._link_document)
        documents_header.addWidget(link_button)
        refresh_documents = QPushButton("Atualizar")
        refresh_documents.clicked.connect(self._refresh_project_documents)
        documents_header.addWidget(refresh_documents)
        documents_layout.addLayout(documents_header)
        self.documents_table = QTableWidget(0, 4)
        self.documents_table.setHorizontalHeaderLabels(["Documento", "Formato", "Situação", "Analisado em"])
        self.documents_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.documents_table.setAlternatingRowColors(True)
        self.documents_table.verticalHeader().setVisible(False)
        self.documents_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.documents_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.documents_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.documents_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        documents_layout.addWidget(self.documents_table, 1)
        self.documents_status = QLabel("Os documentos originais permanecem inalterados.")
        self.documents_status.setObjectName("muted")
        documents_layout.addWidget(self.documents_status)
        self.tabs.addTab(documents_page, "▤  Documentos")
        root.addWidget(self.tabs, 1)

        footer = QHBoxLayout()
        self.status = QLabel("Os dados são armazenados localmente no SQLite.")
        self.status.setObjectName("muted")
        footer.addWidget(self.status, 1)
        local_badge = QLabel("●  ARMAZENAMENTO LOCAL")
        local_badge.setObjectName("eyebrow")
        footer.addWidget(local_badge)
        root.addLayout(footer)
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
            self.grid_count.setText("Nenhuma tabela neste projeto")
            self._refresh_project_documents()

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
        self.grid_count.setText(f"{len(records)} registros · {len(self.columns)} colunas")
        self.status.setText("Banco local SQLite · alterações persistidas automaticamente.")

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
        path, _ = QFileDialog.getOpenFileName(self, "Importar Excel", "", "Excel (*.xlsx *.xlsm *.xls *.xlsb)")
        if not path:
            return
        try:
            extension = Path(path).suffix.lower()
            if extension == ".xls":
                preview = self.exchange.preview_xls(path, limit=4)
            elif extension == ".xlsb":
                preview = self.exchange.preview_xlsb(path, limit=4)
            else:
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
            if extension == ".xls":
                table_ids = self.exchange.import_xls(self.project_id, path)
            elif extension == ".xlsb":
                table_ids = self.exchange.import_xlsb(self.project_id, path)
            else:
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
            self._refresh_project_documents()
        except Exception as exc:
            QMessageBox.warning(self, "Vincular documento", str(exc))

    def _refresh_project_documents(self):
        self.documents_table.setRowCount(0)
        if self.project_id is None:
            self.documents_status.setText("Nenhum projeto selecionado.")
            return
        documents = self.store.list_project_documents(self.project_id)
        self.documents_table.setRowCount(len(documents))
        for row, document in enumerate(documents):
            values = [
                document.get("file_name", ""),
                document.get("extension", ""),
                document.get("status", ""),
                document.get("scanned_at", ""),
            ]
            for column, value in enumerate(values):
                self.documents_table.setItem(row, column, QTableWidgetItem(str(value or "—")))
        self.documents_status.setText(
            f"{len(documents)} documento(s) vinculado(s) · os arquivos originais não são modificados."
        )

    def _show_project_documents(self):
        self._refresh_project_documents()
        self.tabs.setCurrentIndex(1)

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
