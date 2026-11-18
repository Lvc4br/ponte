"""Unified Excel-inspired workspace for PONTE.

The workspace keeps data editing, column filters and linked-document review in
one window. It uses the existing WorkspaceStore and document catalog; it does
not migrate or rewrite legacy records.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QCursor, QDesktopServices, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFormLayout, QHBoxLayout, QInputDialog, QDialog, QDialogButtonBox,
    QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QTextEdit, QHeaderView, QAbstractItemView,
    QScrollArea, QStackedWidget, QProgressDialog,
)

from app.documents.index import DocumentIndex
from app.workspace.exchange import SpreadsheetExchange
from app.workspace.store import WorkspaceStore
from app.workspace.spreadsheet import matches_condition, parse_cell_value
from app.workspace.technical_filters import matches_technical_filters, parse_filter_number


STYLE = """
QMainWindow, QWidget { background:#202832; color:#e8edf3; font-family:'Segoe UI'; font-size:10pt; }
QWidget#ribbon { background:#293543; border:1px solid #3b4b5c; }
QLabel#brand { color:#f0b45d; font-size:19px; font-weight:800; letter-spacing:1px; }
QLabel#muted { color:#9eacbb; }
QPushButton, QComboBox { background:#354557; color:#edf3f8; border:1px solid #4a5d70; border-radius:4px; padding:7px 11px; }
QPushButton:hover { background:#435a70; border-color:#d49a4e; }
QPushButton#primary { background:#b97732; color:white; font-weight:700; border-color:#d89a4d; }
QLineEdit, QTextEdit { background:#18212b; color:#edf3f8; border:1px solid #46586b; border-radius:4px; padding:6px; selection-background-color:#94652f; }
QTableWidget { background:#18212b; alternate-background-color:#202c38; color:#e8edf3; gridline-color:#344454; selection-background-color:#76532f; selection-color:white; border:1px solid #405164; }
QHeaderView::section { background:#35485a; color:#f3f6f8; padding:8px; border:0; border-right:1px solid #4b5c6d; border-bottom:1px solid #526477; font-weight:700; }
QTreeWidget { background:#18212b; alternate-background-color:#202c38; border:1px solid #405164; }
QMenu { background:#293543; color:#edf3f8; border:1px solid #526477; }
QMenu::item:selected { background:#76532f; }
"""


class SpreadsheetGrid(QTableWidget):
    """Spreadsheet grid with TSV copy/paste and history shortcuts."""

    undo_requested = Signal()
    redo_requested = Signal()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo_requested.emit()
            return
        if event.matches(QKeySequence.StandardKey.Redo):
            self.redo_requested.emit()
            return
        if event.matches(QKeySequence.StandardKey.Copy):
            ranges = self.selectedRanges()
            if not ranges:
                return
            selected = ranges[0]
            lines = []
            for row in range(selected.topRow(), selected.bottomRow() + 1):
                values = []
                for col in range(selected.leftColumn(), selected.rightColumn() + 1):
                    item = self.item(row, col)
                    values.append(item.text() if item else "")
                lines.append("\t".join(values))
            QApplication.clipboard().setText("\n".join(lines))
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            raw = QApplication.clipboard().text()
            if not raw:
                return
            start_row, start_col = max(0, self.currentRow()), max(1, self.currentColumn())
            for row_offset, line in enumerate(raw.splitlines()):
                for col_offset, value in enumerate(line.split("\t")):
                    row, col = start_row + row_offset, start_col + col_offset
                    if row >= self.rowCount() or col >= self.columnCount():
                        continue
                    target = self.item(row, col)
                    if target is not None and target.flags() & Qt.ItemFlag.ItemIsEditable:
                        target.setText(value)
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            return
        super().keyPressEvent(event)


class SpreadsheetWindow(QMainWindow):
    """Single-window workspace inspired by spreadsheet interaction patterns."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PONTE | Espaço de trabalho")
        self.resize(1580, 960)
        self.setMinimumSize(1100, 680)
        self.store = WorkspaceStore()
        self.documents = DocumentIndex()
        self.exchange = SpreadsheetExchange(self.store)
        self.project_id = None
        self.table_id = None
        self.columns = []
        self._loading = False
        self._records = []
        self._filters: dict[str, set[str]] = {}
        self._conditions: dict[str, tuple[str, object]] = {}
        self._undo_stack = []
        self._redo_stack = []
        self._history_limit = 500
        self._sort_column = None
        self._sort_descending = False
        self._technical_criteria = {}
        self._legacy_window = None
        self._pdf_document = None
        self._pdf_page_index = 0
        self._scan_worker = None
        self._scan_progress = None
        self._build()
        self._load_projects()

    def _build(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(6)

        ribbon = QWidget()
        ribbon.setObjectName("ribbon")
        ribbon_layout = QVBoxLayout(ribbon)
        ribbon_layout.setContentsMargins(14, 9, 14, 10)
        brand_row = QHBoxLayout()
        brand = QLabel("PONTE")
        brand.setObjectName("brand")
        brand_row.addWidget(brand)
        brand_row.addWidget(QLabel("GERENCIADOR DE DADOS E DOCUMENTOS"))
        brand_row.addStretch()
        self.project_label = QLabel("Projeto local")
        self.project_label.setObjectName("muted")
        brand_row.addWidget(self.project_label)
        ribbon_layout.addLayout(brand_row)

        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("Projeto"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._project_changed)
        selectors.addWidget(self.project_combo, 2)
        selectors.addWidget(QLabel("Tabela"))
        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self._table_changed)
        selectors.addWidget(self.table_combo, 2)
        selectors.addWidget(QLabel("Localizar"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar em todas as colunas…")
        self.search_input.textChanged.connect(self._refresh_grid)
        selectors.addWidget(self.search_input, 3)
        ribbon_layout.addLayout(selectors)

        actions = QHBoxLayout()
        buttons = [
            ("＋ Novo projeto", self._new_project),
            ("＋ Nova tabela", self._new_table),
            ("＋ Coluna", self._new_column),
            ("＋ Registro", self._new_record),
            ("Coluna calculada", self._new_formula_column),
            ("Desfazer", self._undo),
            ("Refazer", self._redo),
            ("Excluir linhas", self._delete_selected),
            ("Importar Excel", self._import_excel),
            ("Exportar Excel", self._export_excel),
            ("Documentos +", self._link_document),
            ("Base legada", self._open_legacy),
        ]
        for label, callback in buttons:
            button = QPushButton(label)
            if label == "＋ Registro":
                button.setObjectName("primary")
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        ribbon_layout.addLayout(actions)
        layout.addWidget(ribbon)

        filters_bar = QWidget()
        filters_bar.setObjectName("filterBar")
        filters_layout = QHBoxLayout(filters_bar)
        filters_layout.setContentsMargins(10, 7, 10, 7)
        filters_layout.setSpacing(7)
        filters_title = QLabel("FILTROS TÉCNICOS")
        filters_title.setObjectName("muted")
        filters_layout.addWidget(filters_title)
        self.type_filter_input = QLineEdit()
        self.type_filter_input.setPlaceholderText("Tipo de obra")
        self.type_filter_input.setMaximumWidth(150)
        filters_layout.addWidget(self.type_filter_input)
        self.technical_filter_inputs = {}
        for key, label in [
            ("width", "Largura (m)"),
            ("span", "Vão (m)"),
            ("length", "Comprimento (m)"),
        ]:
            filters_layout.addWidget(QLabel(label))
            minimum = QLineEdit()
            minimum.setPlaceholderText("Mín.")
            minimum.setMaximumWidth(68)
            maximum = QLineEdit()
            maximum.setPlaceholderText("Máx.")
            maximum.setMaximumWidth(68)
            filters_layout.addWidget(minimum)
            filters_layout.addWidget(maximum)
            self.technical_filter_inputs[key] = (minimum, maximum)
        apply_filters_button = QPushButton("Aplicar")
        apply_filters_button.setObjectName("primary")
        apply_filters_button.clicked.connect(self._apply_technical_filters)
        filters_layout.addWidget(apply_filters_button)
        clear_filters_button = QPushButton("Limpar")
        clear_filters_button.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_filters_button)
        layout.addWidget(filters_bar)

        formula_row = QHBoxLayout()
        self.name_box = QLabel("A1")
        self.name_box.setMinimumWidth(58)
        self.name_box.setStyleSheet("background:#35485a;padding:7px;border:1px solid #526477;")
        formula_row.addWidget(self.name_box)
        formula_row.addWidget(QLabel("fx"))
        self.formula_bar = QLineEdit()
        self.formula_bar.setPlaceholderText("Conteúdo da célula selecionada")
        self.formula_bar.returnPressed.connect(self._apply_formula_bar)
        formula_row.addWidget(self.formula_bar, 1)
        layout.addLayout(formula_row)

        self.grid = SpreadsheetGrid(0, 0)
        self.grid.setAlternatingRowColors(True)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.EditKeyPressed |
            QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.grid.horizontalHeader().setDefaultSectionSize(155)
        self.grid.horizontalHeader().setMinimumSectionSize(75)
        self.grid.horizontalHeader().sectionClicked.connect(self._header_clicked)
        self.grid.itemChanged.connect(self._cell_changed)
        self.grid.currentCellChanged.connect(self._selection_changed)
        self.grid.undo_requested.connect(self._undo)
        self.grid.redo_requested.connect(self._redo)

        docs_split = QSplitter(Qt.Orientation.Vertical)
        docs_split.addWidget(self.grid)
        doc_panel = QWidget()
        doc_layout = QVBoxLayout(doc_panel)
        doc_layout.setContentsMargins(0, 5, 0, 0)
        doc_head = QHBoxLayout()
        doc_head.addWidget(QLabel("DOCUMENTOS DO PROJETO"))
        doc_head.addStretch()
        self.pdf_previous = QPushButton("◀ Página")
        self.pdf_previous.clicked.connect(self._pdf_previous)
        self.pdf_next = QPushButton("Página ▶")
        self.pdf_next.clicked.connect(self._pdf_next)
        self.pdf_page_label = QLabel("")
        doc_head.addWidget(self.pdf_previous)
        doc_head.addWidget(self.pdf_page_label)
        doc_head.addWidget(self.pdf_next)
        open_button = QPushButton("Abrir arquivo")
        open_button.clicked.connect(self._open_document)
        doc_head.addWidget(open_button)
        scan_button = QPushButton("Analisar arquivos")
        scan_button.clicked.connect(self._scan_documents)
        doc_head.addWidget(scan_button)
        refresh_button = QPushButton("Atualizar")
        refresh_button.clicked.connect(self._refresh_documents)
        doc_head.addWidget(refresh_button)
        doc_layout.addLayout(doc_head)
        doc_body = QSplitter(Qt.Orientation.Horizontal)
        self.document_tree = QTreeWidget()
        self.document_tree.setHeaderLabels(["Documento vinculado"])
        self.document_tree.currentItemChanged.connect(self._document_selected)
        self.document_preview = QTextEdit()
        self.document_preview.setReadOnly(True)
        self.document_preview.setPlaceholderText("Selecione um documento para consultar o conteúdo extraído.")
        self.pdf_preview = QLabel("Pré-visualização de PDF")
        self.pdf_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_scroll = QScrollArea()
        self.pdf_scroll.setWidgetResizable(True)
        self.pdf_scroll.setWidget(self.pdf_preview)
        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(self.document_preview)
        self.preview_stack.addWidget(self.pdf_scroll)
        doc_body.addWidget(self.document_tree)
        doc_body.addWidget(self.preview_stack)
        doc_body.setSizes([360, 900])
        doc_layout.addWidget(doc_body, 1)
        docs_split.addWidget(doc_panel)
        docs_split.setSizes([650, 230])
        layout.addWidget(docs_split, 1)

        self.status = QLabel("Pronto")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)
        self.setCentralWidget(root)
        self.setStyleSheet(STYLE + "\\nQWidget#filterBar { background:#293543; border:1px solid #3b4b5c; border-radius:4px; }")
        self.statusBar().showMessage("Banco local preservado · alterações salvas automaticamente")

    def _load_projects(self, selected=None):
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        projects = self.store.list_projects()
        if not projects:
            project_id = self.store.create_project("Meu espaço de dados")
            projects = self.store.list_projects()
            selected = project_id
        for project in projects:
            self.project_combo.addItem(project["name"], project["id"])
        index = self.project_combo.findData(selected) if selected else 0
        self.project_combo.setCurrentIndex(max(0, index))
        self.project_combo.blockSignals(False)
        self._project_changed(self.project_combo.currentIndex())

    def _project_changed(self, index):
        if index < 0:
            return
        self.project_id = self.project_combo.currentData()
        self.project_label.setText(self.project_combo.currentText())
        self.table_combo.blockSignals(True)
        self.table_combo.clear()
        for table in self.store.list_tables(self.project_id):
            self.table_combo.addItem(table["name"], table["id"])
        self.table_combo.blockSignals(False)
        self.table_id = self.table_combo.currentData()
        self._filters.clear()
        self._conditions.clear()
        self._refresh_grid()
        self._refresh_documents()

    def _table_changed(self, index):
        self.table_id = self.table_combo.currentData() if index >= 0 else None
        self._filters.clear()
        self._conditions.clear()
        self._refresh_grid()

    def _technical_filter_criteria(self):
        criteria = {}
        requested_type = self.type_filter_input.text().strip()
        if requested_type:
            criteria["type_obra"] = requested_type
        labels = {"width": "Largura", "span": "Vão", "length": "Comprimento total"}
        for key, (minimum_input, maximum_input) in self.technical_filter_inputs.items():
            minimum_raw, maximum_raw = minimum_input.text().strip(), maximum_input.text().strip()
            minimum = parse_filter_number(minimum_raw) if minimum_raw else None
            maximum = parse_filter_number(maximum_raw) if maximum_raw else None
            if minimum_raw and minimum is None:
                raise ValueError(f"{labels[key]}: informe um número válido para o mínimo.")
            if maximum_raw and maximum is None:
                raise ValueError(f"{labels[key]}: informe um número válido para o máximo.")
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"{labels[key]}: o mínimo não pode ser maior que o máximo.")
            if minimum is not None:
                criteria[f"{key}_min" if key != "span" else "span_min"] = minimum
            if maximum is not None:
                criteria[f"{key}_max" if key != "span" else "span_max"] = maximum
        return criteria

    def _apply_technical_filters(self):
        try:
            self._technical_criteria = self._technical_filter_criteria()
            self._refresh_grid()
        except ValueError as exc:
            QMessageBox.warning(self, "Filtros inválidos", str(exc))

    def _refresh_grid(self, *_):
        if self.table_id is None:
            self.columns, self._records = [], []
            self._loading = True
            self.grid.clear()
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self._loading = False
            self.status.setText("Este projeto ainda não possui tabelas. Use “Nova tabela”.")
            return
        try:
            self.columns = self.store.list_columns(self.table_id)
            records = self.store.list_records(self.table_id)
            total_records = len(records)
            query = self.search_input.text().strip().casefold()
            if query:
                records = [
                    record for record in records
                    if any(query in str(value).casefold() for value in record["values"].values() if value is not None)
                ]
            for name, allowed in self._filters.items():
                records = [record for record in records if str(record["values"].get(name, "")) in allowed]
            for name, (operator, target) in self._conditions.items():
                records = [record for record in records if self._matches_condition(record["values"].get(name), operator, target)]
            if self._technical_criteria:
                records = [record for record in records if matches_technical_filters(record["values"], self._technical_criteria)]
            if self._sort_column:
                sort_column = next((c for c in self.columns if c["name"] == self._sort_column), None)
                numeric = bool(sort_column and sort_column["data_type"] in {"integer", "decimal"})
                records.sort(
                    key=lambda record: (
                        record["values"].get(self._sort_column) is None,
                        (float(record["values"].get(self._sort_column) or 0) if numeric
                         else str(record["values"].get(self._sort_column) or "").casefold()),
                    ),
                    reverse=self._sort_descending,
                )
            self._records = records
            self._loading = True
            self.grid.clear()
            self.grid.setColumnCount(len(self.columns) + 1)
            self.grid.setHorizontalHeaderLabels(["ID"] + [
                f"{column['name']}  ▾" for column in self.columns
            ])
            self.grid.setColumnHidden(0, True)
            self.grid.setRowCount(len(records))
            for row, record in enumerate(records):
                id_item = QTableWidgetItem(str(record["id"]))
                id_item.setData(Qt.ItemDataRole.UserRole, record["id"])
                self.grid.setItem(row, 0, id_item)
                for col, column in enumerate(self.columns, start=1):
                    value = record["values"].get(column["name"])
                    item = QTableWidgetItem("" if value is None else str(value))
                    item.setData(Qt.ItemDataRole.UserRole, column["name"])
                    item.setData(Qt.ItemDataRole.UserRole + 1, value)
                    if column.get("formula"):
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setToolTip(f"Coluna calculada · {column['formula']}")
                    self.grid.setItem(row, col, item)
            self._loading = False
            active = len(self._filters) + len(self._conditions) + len(self._technical_criteria)
            self.status.setText(
                f"{len(records)} de {total_records} registros · "
                f"{len(self.columns)} colunas · {active} filtro(s) ativo(s) · "
                f"{len(self._undo_stack)} ação(ões) para desfazer"
            )
        except Exception as exc:
            self._loading = False
            QMessageBox.warning(self, "Tabela", str(exc))

    def _header_clicked(self, section):
        if section == 0 or section > len(self.columns):
            return
        column = self.columns[section - 1]
        menu = QMenu(self)
        name = column["name"]
        sort_asc = menu.addAction("Ordenar de A a Z / menor a maior")
        sort_desc = menu.addAction("Ordenar de Z a A / maior a menor")
        menu.addSeparator()
        search_action = menu.addAction("Pesquisar valor…")
        condition_action = menu.addAction("Filtrar por condição…")
        menu.addSeparator()
        all_action = menu.addAction("Selecionar todos os valores")
        clear_action = menu.addAction("Limpar filtro desta coluna")
        menu.addSeparator()
        values = sorted(
            {str(record["values"].get(name, "")) for record in self.store.list_records(self.table_id)},
            key=str.casefold,
        )
        selected = self._filters.get(name, set(values))
        value_actions = {}
        for value in values[:250]:
            action = menu.addAction(("☑ " if value in selected else "☐ ") + (value or "(vazio)"))
            action.setCheckable(True)
            action.setChecked(value in selected)
            value_actions[action] = value
        chosen = menu.exec(QCursor.pos())
        if chosen == sort_asc:
            self._sort_column, self._sort_descending = name, False
        elif chosen == sort_desc:
            self._sort_column, self._sort_descending = name, True
        elif chosen == search_action:
            text, ok = QInputDialog.getText(self, "Pesquisar filtro", f"Valor em “{name}” contém:")
            if ok:
                if text.strip():
                    self._filters[name] = {
                        value for value in values if text.casefold() in value.casefold()
                    }
                else:
                    self._filters.pop(name, None)
                self._conditions.pop(name, None)
        elif chosen == condition_action:
            self._set_column_condition(column)
        elif chosen == all_action:
            self._filters.pop(name, None)
            self._conditions.pop(name, None)
        elif chosen == clear_action:
            self._filters.pop(name, None)
            self._conditions.pop(name, None)
        elif chosen in value_actions:
            new_selected = set(selected)
            for action, value in value_actions.items():
                if action.isChecked():
                    new_selected.add(value)
                else:
                    new_selected.discard(value)
            if len(new_selected) == len(values):
                self._filters.pop(name, None)
            else:
                self._filters[name] = new_selected
            self._conditions.pop(name, None)
        else:
            return
        self._refresh_grid()

    def _selection_changed(self, row, column, *_):
        if row < 0 or column <= 0:
            self.name_box.setText("")
            self.formula_bar.clear()
            return
        item = self.grid.item(row, column)
        self.name_box.setText(f"{self._column_letter(column)}{row + 1}")
        self.formula_bar.setText(item.text() if item else "")

    @staticmethod
    def _column_letter(number):
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _apply_formula_bar(self):
        row, col = self.grid.currentRow(), self.grid.currentColumn()
        if row < 0 or col <= 0:
            return
        item = self.grid.item(row, col)
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEditable:
            item.setText(self.formula_bar.text())

    def _cell_changed(self, item):
        if self._loading or item.column() <= 0 or self.table_id is None:
            return
        try:
            record_id = self.grid.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            column = self.columns[item.column() - 1]
            value = self._parse_value(item.text(), column["data_type"])
            previous = item.data(Qt.ItemDataRole.UserRole + 1)
            self.store.update_record(record_id, {column["name"]: value})
            previous_text = "" if previous is None else str(previous)
            if previous_text != item.text():
                self._undo_stack.append({
                    "record_id": record_id, "column": column["name"],
                    "old": previous, "new": value,
                })
                self._undo_stack = self._undo_stack[-self._history_limit:]
                self._redo_stack.clear()
            item.setData(Qt.ItemDataRole.UserRole + 1, item.text())
            self.status.setText(f"Registro {record_id} salvo automaticamente.")
        except Exception as exc:
            QMessageBox.warning(self, "Valor inválido", str(exc))
            self._refresh_grid()

    @staticmethod
    def _parse_value(raw, data_type):
        return parse_cell_value(raw, data_type)

    def _new_project(self):
        name, ok = QInputDialog.getText(self, "Novo projeto", "Nome:")
        if ok:
            try:
                project_id = self.store.create_project(name)
                self._load_projects(project_id)
            except Exception as exc:
                QMessageBox.warning(self, "Projeto", str(exc))

    def _new_table(self):
        if self.project_id is None:
            return
        name, ok = QInputDialog.getText(self, "Nova tabela", "Nome da tabela:")
        if ok:
            try:
                table_id = self.store.create_table(self.project_id, name)
                self._project_changed(self.project_combo.currentIndex())
                self.table_combo.setCurrentIndex(self.table_combo.findData(table_id))
            except Exception as exc:
                QMessageBox.warning(self, "Tabela", str(exc))

    def _new_column(self):
        if self.table_id is None:
            QMessageBox.information(self, "Coluna", "Crie ou selecione uma tabela primeiro.")
            return
        name, ok = QInputDialog.getText(self, "Nova coluna", "Nome:")
        if not ok:
            return
        kind, ok = QInputDialog.getItem(
            self, "Tipo de coluna", "Tipo:",
            ["text", "integer", "decimal", "boolean", "date", "datetime", "json"], 0, False
        )
        if ok:
            try:
                self.store.add_column(self.table_id, name, kind)
                self._refresh_grid()
            except Exception as exc:
                QMessageBox.warning(self, "Coluna", str(exc))

    def _new_record(self):
        if self.table_id is None or not self.columns:
            QMessageBox.information(self, "Registro", "Crie uma tabela com ao menos uma coluna.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Novo registro")
        dialog.setMinimumWidth(520)
        form = QFormLayout(dialog)
        editors = {}
        for column in self.columns:
            if column.get("formula"):
                continue
            editor = QLineEdit()
            editor.setPlaceholderText(
                f"{column['data_type']}" + (" · obrigatório" if column["required"] else " · opcional")
            )
            form.addRow(column["name"], editor)
            editors[column["name"]] = (editor, column)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar registro")
        buttons.accepted.connect(lambda: self._submit_new_record(dialog, editors))
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.exec()

    def _submit_new_record(self, dialog, editors):
        values = {}
        try:
            for name, (editor, column) in editors.items():
                raw = editor.text().strip()
                if not raw:
                    if column["required"]:
                        raise ValueError(f"O campo “{name}” é obrigatório.")
                    if column["default"] is not None:
                        continue
                    values[name] = None
                else:
                    values[name] = self._parse_value(raw, column["data_type"])
            self.store.insert_record(self.table_id, values)
            dialog.accept()
            self._refresh_grid()
            self.status.setText("Novo registro salvo.")
        except Exception as exc:
            QMessageBox.warning(dialog, "Não foi possível salvar", str(exc))

    def _delete_selected(self):
        rows = sorted({index.row() for index in self.grid.selectionModel().selectedIndexes()})
        if not rows and self.grid.currentRow() >= 0:
            rows = [self.grid.currentRow()]
        ids = [
            self.grid.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in rows if self.grid.item(row, 0)
        ]
        if not ids:
            return
        answer = QMessageBox.question(
            self, "Excluir registros",
            f"Excluir {len(ids)} registro(s) selecionado(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            for record_id in ids:
                self.store.delete_record(record_id)
            self._refresh_grid()

    def _import_excel(self):
        if self.project_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar planilha", "", "Planilhas (*.xlsx *.xlsm *.xls *.xlsb)"
        )
        if not path:
            return
        try:
            suffix = Path(path).suffix.casefold()
            if suffix == ".xls":
                preview = self.exchange.preview_xls(path, limit=3)
                ids = self.exchange.import_xls(self.project_id, path)
            elif suffix == ".xlsb":
                preview = self.exchange.preview_xlsb(path, limit=3)
                ids = self.exchange.import_xlsb(self.project_id, path)
            else:
                preview = self.exchange.preview_xlsx(path, limit=3)
                ids = self.exchange.import_xlsx(self.project_id, path)
            QMessageBox.information(
                self, "Importação concluída",
                f"{Path(path).name}\n{len(ids)} aba(s) importada(s) como tabela(s)."
            )
            self._project_changed(self.project_combo.currentIndex())
            if ids:
                self.table_combo.setCurrentIndex(self.table_combo.findData(ids[0]))
        except Exception as exc:
            QMessageBox.warning(self, "Importar Excel", str(exc))

    def _export_excel(self):
        if self.table_id is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Excel", "", "Excel (*.xlsx)")
        if path:
            try:
                self.exchange.export_xlsx(self.table_id, path)
                self.status.setText(f"Planilha exportada: {path}")
            except Exception as exc:
                QMessageBox.warning(self, "Exportar Excel", str(exc))

    @staticmethod
    def _matches_condition(value, operator, target):
        return matches_condition(value, operator, target)

    def _set_column_condition(self, column):
        name, kind = column["name"], column["data_type"]
        if kind in {"integer", "decimal"}:
            operators = ["igual a", "diferente de", "maior que", "maior ou igual a",
                         "menor que", "menor ou igual a", "está vazio", "não está vazio"]
        elif kind in {"date", "datetime"}:
            operators = ["igual a", "diferente de", "depois de", "antes de",
                         "está vazio", "não está vazio"]
        elif kind == "boolean":
            operators = ["igual a", "diferente de", "está vazio", "não está vazio"]
        else:
            operators = ["contém", "começa com", "igual a", "diferente de",
                         "está vazio", "não está vazio"]
        operator, ok = QInputDialog.getItem(
            self, "Filtro por condição", f"Condição para “{name}”:", operators, 0, False
        )
        if not ok:
            return
        target = None
        if operator not in {"está vazio", "não está vazio"}:
            raw, ok = QInputDialog.getText(self, "Valor do filtro", f"Valor ({kind}):")
            if not ok:
                return
            try:
                if kind in {"integer", "decimal", "boolean"}:
                    target = self._parse_value(raw, kind)
                elif kind in {"date", "datetime"}:
                    target = raw.strip()
                    from datetime import date, datetime
                    parser = datetime.fromisoformat if kind == "datetime" else date.fromisoformat
                    parser(target)
                else:
                    target = raw
                if operator == "depois de":
                    operator = "maior que"
                elif operator == "antes de":
                    operator = "menor que"
                self._conditions[name] = (operator, target)
                self._filters.pop(name, None)
                self._refresh_grid()
            except Exception as exc:
                QMessageBox.warning(self, "Filtro inválido", str(exc))

    def _apply_history_entry(self, entry, value, destination):
        try:
            if not self.store.update_record(entry["record_id"], {entry["column"]: value}):
                raise ValueError("O registro não existe mais.")
            destination.append(entry)
            self._refresh_grid()
        except Exception as exc:
            QMessageBox.warning(self, "Histórico", f"Não foi possível aplicar a alteração: {exc}")

    def _undo(self):
        if not self._undo_stack:
            return
        entry = self._undo_stack.pop()
        self._apply_history_entry(entry, entry["old"], self._redo_stack)

    def _redo(self):
        if not self._redo_stack:
            return
        entry = self._redo_stack.pop()
        self._apply_history_entry(entry, entry["new"], self._undo_stack)

    def _clear_filters(self):
        self._filters.clear()
        self._conditions.clear()
        self._technical_criteria.clear()
        self.type_filter_input.clear()
        for minimum, maximum in self.technical_filter_inputs.values():
            minimum.clear()
            maximum.clear()
        self.search_input.clear()
        self._sort_column = None
        self._sort_descending = False
        self._refresh_grid()

    def _new_formula_column(self):
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

    def _scan_documents(self):
        if self.project_id is None:
            QMessageBox.information(self, "Analisar documentos", "Selecione um projeto primeiro.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar documentos para análise", "",
            "Documentos suportados (*.pdf *.doc *.docx *.ppt *.pptx *.rtf *.odt *.odp "
            "*.xlsx *.xlsm *.xls *.xlsb *.csv *.txt *.md *.json *.xml *.dxf *.dwg "
            "*.ifc *.rvt *.rfa *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.gif);;"
            "Todos os arquivos (*.*)"
        )
        if not paths:
            return
        try:
            from app.ui.main_window import DocumentScanWorker
            self._scan_worker = DocumentScanWorker(paths, self)
            self._scan_progress = QProgressDialog(
                "Preparando análise documental…", "Cancelar", 0, 0, self
            )
            self._scan_progress.setWindowTitle("Análise de documentos")
            self._scan_progress.setWindowModality(Qt.WindowModality.WindowModal)
            self._scan_progress.canceled.connect(self._scan_worker.cancel)
            self._scan_worker.progress.connect(self._scan_progress_update)
            self._scan_worker.completed.connect(self._scan_completed)
            self._scan_progress.show()
            self._scan_worker.start()
        except Exception as exc:
            QMessageBox.warning(self, "Análise documental", str(exc))

    def _scan_progress_update(self, current, total, file_name):
        if self._scan_progress is None:
            return
        self._scan_progress.setRange(0, max(1, total))
        self._scan_progress.setValue(current)
        self._scan_progress.setLabelText(f"Analisando {current} de {total}: {file_name}")

    def _scan_completed(self, results):
        linked = 0
        failures = []
        try:
            for result in results:
                if not result.sha256:
                    failures.append(result.file_name)
                    continue
                document_id = self.documents.index_result(result)
                if self.store.link_document(self.project_id, document_id):
                    linked += 1
                if result.status == "error":
                    failures.append(result.file_name)
            self._refresh_documents()
            self.status.setText(
                f"{len(results)} arquivo(s) analisado(s) · {linked} novo(s) vínculo(s) documental(is)"
            )
            if failures:
                QMessageBox.warning(
                    self, "Análise concluída com avisos",
                    "Não foi possível analisar completamente:\n" + "\n".join(failures[:20])
                )
        except Exception as exc:
            QMessageBox.warning(self, "Análise documental", str(exc))
        finally:
            if self._scan_progress is not None:
                self._scan_progress.close()
            self._scan_progress = None
            self._scan_worker = None

    def _refresh_documents(self):
        self.document_tree.clear()
        if self.project_id is None:
            return
        for document in self.store.list_project_documents(self.project_id):
            item = QTreeWidgetItem([
                f"{document['file_name']} · {document['status']} · {document['extension']}"
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, document["id"])
            self.document_tree.addTopLevelItem(item)
        self.document_preview.setPlainText(
            f"{self.document_tree.topLevelItemCount()} documento(s) vinculado(s) a este projeto."
        )

    def _document_selected(self, current, _previous):
        if current is None:
            return
        document_id = current.data(0, Qt.ItemDataRole.UserRole)
        document = self.documents.get_document(document_id)
        if not document:
            return
        self._close_pdf_preview()
        summary = {
            "arquivo": document["file_name"],
            "caminho": document["path"],
            "formato": document["extension"],
            "status": document["status"],
            "metadados": document["metadata"],
            "avisos": document["warnings"],
            "erros": document["errors"],
            "conteudo_extraido": document["sections"],
        }
        self.document_preview.setPlainText(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        if document["extension"].casefold() == ".pdf" and Path(document["path"]).exists():
            try:
                import pypdfium2 as pdfium
                self._pdf_document = pdfium.PdfDocument(document["path"])
                self._pdf_page_index = 0
                self._render_pdf_page()
                self.preview_stack.setCurrentWidget(self.pdf_scroll)
                return
            except Exception as exc:
                self.document_preview.setPlainText(
                    f"Não foi possível pré-visualizar este PDF: {exc}\n\n"
                    + json.dumps(summary, ensure_ascii=False, indent=2, default=str)
                )
        self.preview_stack.setCurrentWidget(self.document_preview)
        self.pdf_page_label.setText("")

    def _close_pdf_preview(self):
        if self._pdf_document is not None:
            try:
                self._pdf_document.close()
            except Exception:
                pass
        self._pdf_document = None
        self._pdf_page_index = 0

    def _render_pdf_page(self):
        if self._pdf_document is None:
            return
        try:
            from io import BytesIO
            page = self._pdf_document[self._pdf_page_index]
            bitmap = page.render(scale=1.35)
            image = bitmap.to_pil()
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            pixmap = QPixmap()
            if not pixmap.loadFromData(buffer.getvalue(), "PNG"):
                raise ValueError("Não foi possível converter a página do PDF.")
            self.pdf_preview.setPixmap(pixmap)
            self.pdf_page_label.setText(
                f"{self._pdf_page_index + 1} / {len(self._pdf_document)}"
            )
            self.pdf_previous.setEnabled(self._pdf_page_index > 0)
            self.pdf_next.setEnabled(self._pdf_page_index + 1 < len(self._pdf_document))
        except Exception as exc:
            self.document_preview.setPlainText(f"Erro ao renderizar a página do PDF: {exc}")
            self.preview_stack.setCurrentWidget(self.document_preview)

    def _pdf_previous(self):
        if self._pdf_document is not None and self._pdf_page_index > 0:
            self._pdf_page_index -= 1
            self._render_pdf_page()

    def _pdf_next(self):
        if self._pdf_document is not None and self._pdf_page_index + 1 < len(self._pdf_document):
            self._pdf_page_index += 1
            self._render_pdf_page()

    def _link_document(self):
        if self.project_id is None:
            return
        available = self.documents.list_documents()
        if not available:
            QMessageBox.information(
                self, "Documentos", "Nenhum documento foi analisado ainda. Use a janela Base legada para iniciar a análise documental."
            )
            return
        labels = [f"{doc['file_name']} · {doc['status']} · ID {doc['id']}" for doc in available]
        label, ok = QInputDialog.getItem(self, "Vincular documento", "Documento:", labels, 0, False)
        if ok:
            document = available[labels.index(label)]
            self.store.link_document(self.project_id, document["id"])
            self._refresh_documents()

    def _open_document(self):
        item = self.document_tree.currentItem()
        if item is None:
            return
        document = self.documents.get_document(item.data(0, Qt.ItemDataRole.UserRole))
        if document and Path(document["path"]).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(document["path"]))
        elif document:
            QMessageBox.warning(self, "Arquivo não encontrado", document["path"])

    def _open_legacy(self):
        try:
            from app.ui.main_window import MainWindow
            self._legacy_window = MainWindow()
            self._legacy_window.show()
            self._legacy_window.raise_()
            self._legacy_window.activateWindow()
        except Exception as exc:
            QMessageBox.warning(self, "Base legada", str(exc))

