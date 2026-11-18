"""Basic desktop workspace for generic projects and editable data tables."""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app.workspace.exchange import SpreadsheetExchange


class WorkspaceDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
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
        root.addLayout(project_row)

        table_row = QHBoxLayout()
        table_row.addWidget(QLabel("Tabela"))
        self.tables = QComboBox()
        self.tables.currentIndexChanged.connect(self._table_changed)
        table_row.addWidget(self.tables, 1)
        for label, callback in (
            ("Nova tabela", self._add_table),
            ("Nova coluna", self._add_column),
            ("Coluna calculada", self._add_formula_column),
            ("Novo registro", self._add_record),
            ("Excluir registro", self._delete_record),
            ("Importar CSV", self._import_csv),
            ("Importar Excel", self._import_xlsx),
            ("Exportar CSV", self._export_csv),
            ("Exportar Excel", self._export_xlsx),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            table_row.addWidget(button)
        root.addLayout(table_row)

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
        labels = {c["name"]: c["data_type"] for c in self.columns}
        template = {c["name"]: c["default"] for c in self.columns}
        raw, ok = QInputDialog.getMultiLineText(
            self, "Novo registro", "Valores em JSON (use os nomes das colunas):",
            json.dumps(template, ensure_ascii=False, indent=2)
        )
        if not ok:
            return
        try:
            values = json.loads(raw)
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
            table_ids = self.exchange.import_xlsx(self.project_id, path)
            self._project_changed(self.projects.currentIndex())
            if table_ids:
                self.tables.setCurrentIndex(self.tables.findData(table_ids[0]))
        except Exception as exc:
            QMessageBox.warning(self, "Importação Excel", str(exc))

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
