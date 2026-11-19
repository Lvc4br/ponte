"""Three-column engineering workspace built on the existing spreadsheet workflow.

This window rearranges the existing SpreadsheetWindow actions without replacing
its storage, import/export, document indexing, filtering, editing or history
services. The right rail summarizes the exact filtered record set.
"""
from __future__ import annotations

from statistics import mean, median
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QHeaderView, QStackedWidget,
)

from app.ui.spreadsheet_window import SpreadsheetWindow, SpreadsheetGrid
from app.workspace.technical_filters import parse_filter_number


from app.workspace.analytics_summary import summarize_numeric_columns


DASHBOARD_STYLE = """
QMainWindow, QWidget {
    background: #151e28; color: #e8eef4;
    font-family: 'Segoe UI'; font-size: 9pt;
}
QFrame#topbar, QFrame#panel {
    background: #1d2936; border: 1px solid #344657; border-radius: 7px;
}
QLabel#brand { color: #e69a43; font-size: 18px; font-weight: 800; }
QLabel#muted { color: #a2b1c0; }
QLabel#section { color: #dce5ed; font-size: 10pt; font-weight: 700; }
QLineEdit, QTextEdit, QComboBox {
    background: #18232f; color: #e8eef4; border: 1px solid #405366;
    border-radius: 5px; padding: 6px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #e69a43; }
QPushButton {
    background: #2a3a4b; color: #e8eef4; border: 1px solid #40566a;
    border-radius: 5px; padding: 7px 10px;
}
QPushButton:hover { background: #354b60; border-color: #71879a; }
QPushButton#primary {
    background: #c27b31; color: #ffffff; border-color: #e69a43;
    font-weight: 700;
}
QPushButton#primary:hover { background: #d18a3d; }
QTableWidget {
    background: #18232f; alternate-background-color: #202e3c;
    color: #e8eef4; gridline-color: #344657;
    selection-background-color: #70502f; selection-color: #ffffff;
    border: 1px solid #344657; border-radius: 5px;
}
QHeaderView::section {
    background: #2b4053; color: #f0f4f7; padding: 7px;
    border: 0; border-right: 1px solid #40566a; font-weight: 700;
}
QTreeWidget { background: #18232f; border: 1px solid #344657; }
QMenu { background: #243342; color: #e8eef4; border: 1px solid #52677a; }
QMenu::item:selected { background: #70502f; }
QSplitter::handle { background: #344657; }
"""


class EngineeringWorkspaceWindow(SpreadsheetWindow):
    """Three-column interface; business logic remains in SpreadsheetWindow."""

    def _build(self):
        self.setWindowTitle("Gerenciador de Estruturas | Espaço de trabalho")
        self.resize(1600, 960)
        self.setMinimumSize(1180, 720)

        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(8)

        # Compact application header and project/table selectors.
        header = QFrame()
        header.setObjectName("topbar")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 9, 12, 9)
        header_layout.setSpacing(8)

        title_row = QHBoxLayout()
        brand = QLabel("GERENCIADOR DE ESTRUTURAS")
        brand.setObjectName("brand")
        title_row.addWidget(brand)
        subtitle = QLabel("DADOS  ·  PLANILHAS  ·  DOCUMENTOS")
        subtitle.setObjectName("muted")
        title_row.addWidget(subtitle)
        title_row.addStretch()
        self.project_label = QLabel("Projeto local")
        self.project_label.setObjectName("muted")
        title_row.addWidget(self.project_label)
        header_layout.addLayout(title_row)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Projeto"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._project_changed)
        selector_row.addWidget(self.project_combo, 2)
        selector_row.addWidget(QLabel("Tabela"))
        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self._table_changed)
        selector_row.addWidget(self.table_combo, 2)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar em todas as colunas…")
        self.search_input.textChanged.connect(self._refresh_grid)
        selector_row.addWidget(self.search_input, 3)
        header_layout.addLayout(selector_row)

        actions = QHBoxLayout()
        for label, callback, primary in [
            ("＋ Projeto", self._new_project, False),
            ("＋ Tabela", self._new_table, False),
            ("＋ Registro", self._new_record, True),
            ("Importar Excel", self._import_excel, False),
            ("Exportar Excel", self._export_excel, False),
            ("Documentos", self._link_document, False),
        ]:
            button = QPushButton(label)
            if primary:
                button.setObjectName("primary")
            button.clicked.connect(callback)
            actions.addWidget(button)

        tools_button = QPushButton("Ferramentas  ▾")
        tools_menu = QMenu(tools_button)
        for label, callback in [
            ("Nova coluna", self._new_column),
            ("Coluna calculada", self._new_formula_column),
            ("Desfazer", self._undo),
            ("Refazer", self._redo),
            ("Excluir linhas selecionadas", self._delete_selected),
        ]:
            action = tools_menu.addAction(label)
            action.triggered.connect(callback)
        tools_menu.addSeparator()
        for label, callback in [
            ("Excluir tabela…", self._delete_table),
            ("Excluir projeto…", self._delete_project),
        ]:
            action = tools_menu.addAction(label)
            action.triggered.connect(callback)
        tools_button.setMenu(tools_menu)
        actions.addWidget(tools_button)
        actions.addStretch()
        header_layout.addLayout(actions)
        outer.addWidget(header)

        # Main three-column workspace.
        workspace = QSplitter(Qt.Orientation.Horizontal)
        workspace.setChildrenCollapsible(False)

        # Left rail: technical filters.
        left = QFrame()
        left.setObjectName("panel")
        left.setMinimumWidth(255)
        left.setMaximumWidth(330)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(13, 13, 13, 13)
        left_layout.setSpacing(10)
        filter_title = QLabel("FILTROS TÉCNICOS")
        filter_title.setObjectName("section")
        left_layout.addWidget(filter_title)
        hint = QLabel("Combine critérios para refinar a base.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        left_layout.addWidget(hint)

        self.type_filter_input = QLineEdit()
        self.type_filter_input.setPlaceholderText("Ex.: ponte rodoviária")
        left_layout.addWidget(QLabel("Tipo de obra"))
        left_layout.addWidget(self.type_filter_input)

        self.technical_filter_inputs = {}
        for key, label in [
            ("width", "Largura (m)"),
            ("span", "Vão (m)"),
            ("length", "Comprimento total (m)"),
        ]:
            group = QWidget()
            grid = QGridLayout(group)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(7)
            grid.setVerticalSpacing(4)
            title = QLabel(label)
            minimum = QLineEdit()
            minimum.setPlaceholderText("Mínimo")
            maximum = QLineEdit()
            maximum.setPlaceholderText("Máximo")
            grid.addWidget(title, 0, 0, 1, 2)
            grid.addWidget(minimum, 1, 0)
            grid.addWidget(maximum, 1, 1)
            left_layout.addWidget(group)
            self.technical_filter_inputs[key] = (minimum, maximum)

        left_layout.addStretch()
        apply_button = QPushButton("Aplicar filtros")
        apply_button.setObjectName("primary")
        apply_button.clicked.connect(self._apply_technical_filters)
        left_layout.addWidget(apply_button)
        clear_button = QPushButton("Limpar filtros")
        clear_button.clicked.connect(self._clear_filters)
        left_layout.addWidget(clear_button)
        self.filter_state_label = QLabel("Nenhum filtro técnico aplicado")
        self.filter_state_label.setObjectName("muted")
        self.filter_state_label.setWordWrap(True)
        left_layout.addWidget(self.filter_state_label)
        workspace.addWidget(left)

        # Center: editable spreadsheet and formula bar.
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(2, 0, 2, 0)
        center_layout.setSpacing(7)
        center_heading = QHBoxLayout()
        center_title = QLabel("BASE DE OBRAS")
        center_title.setObjectName("section")
        center_heading.addWidget(center_title)
        center_heading.addStretch()
        self.grid_count = QLabel("0 registros")
        self.grid_count.setObjectName("muted")
        center_heading.addWidget(self.grid_count)
        center_layout.addLayout(center_heading)

        formula_row = QHBoxLayout()
        self.name_box = QLabel("A1")
        self.name_box.setMinimumWidth(48)
        self.name_box.setStyleSheet(
            "background:#2b4053;padding:6px;border:1px solid #40566a;border-radius:4px;"
        )
        formula_row.addWidget(self.name_box)
        formula_row.addWidget(QLabel("fx"))
        self.formula_bar = QLineEdit()
        self.formula_bar.setPlaceholderText("Conteúdo da célula selecionada")
        self.formula_bar.returnPressed.connect(self._apply_formula_bar)
        formula_row.addWidget(self.formula_bar, 1)
        center_layout.addLayout(formula_row)

        self.grid = SpreadsheetGrid(0, 0)
        self.grid.setAlternatingRowColors(True)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.grid.horizontalHeader().setDefaultSectionSize(145)
        self.grid.horizontalHeader().setMinimumSectionSize(72)
        self.grid.horizontalHeader().sectionClicked.connect(self._header_clicked)
        self.grid.itemChanged.connect(self._cell_changed)
        self.grid.currentCellChanged.connect(self._selection_changed)
        self.grid.currentCellChanged.connect(self._update_selected_properties)
        self.grid.undo_requested.connect(self._undo)
        self.grid.redo_requested.connect(self._redo)
        self.grid.paste_requested.connect(self._paste_cells)
        center_layout.addWidget(self.grid, 1)
        workspace.addWidget(center)

        # Right rail: live statistics and selected-row properties.
        right = QFrame()
        right.setObjectName("panel")
        right.setMinimumWidth(300)
        right.setMaximumWidth(390)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        stats_title = QLabel("RESUMO ESTATÍSTICO")
        stats_title.setObjectName("section")
        right_layout.addWidget(stats_title)
        self.indicators_headline = QLabel("0 obras encontradas")
        self.indicators_headline.setStyleSheet("font-size:22px;font-weight:800;color:#e69a43;")
        right_layout.addWidget(self.indicators_headline)
        self.indicators_detail = QLabel("As estatísticas acompanham os filtros e a pesquisa.")
        self.indicators_detail.setObjectName("muted")
        self.indicators_detail.setWordWrap(True)
        right_layout.addWidget(self.indicators_detail)

        self.indicators_table = QTableWidget(0, 6)
        self.indicators_table.setHorizontalHeaderLabels(
            ["Campo", "N", "Média", "Mediana", "Mín.", "Máx."]
        )
        self.indicators_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.indicators_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.indicators_table.verticalHeader().setVisible(False)
        self.indicators_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.indicators_table.horizontalHeader().setStretchLastSection(True)
        self.indicators_table.setMaximumHeight(260)
        right_layout.addWidget(self.indicators_table)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color:#344657;")
        right_layout.addWidget(separator)
        props_title = QLabel("PROPRIEDADES DA OBRA")
        props_title.setObjectName("section")
        right_layout.addWidget(props_title)
        self.properties_view = QTextEdit()
        self.properties_view.setReadOnly(True)
        self.properties_view.setPlaceholderText("Selecione uma linha para consultar os dados completos.")
        right_layout.addWidget(self.properties_view, 1)
        workspace.addWidget(right)

        workspace.setStretchFactor(0, 0)
        workspace.setStretchFactor(1, 1)
        workspace.setStretchFactor(2, 0)
        workspace.setSizes([280, 900, 330])

        # Bottom document area remains available but consumes less space.
        docs_panel = QFrame()
        docs_panel.setObjectName("panel")
        docs_layout = QVBoxLayout(docs_panel)
        docs_layout.setContentsMargins(10, 7, 10, 8)
        docs_layout.setSpacing(6)
        docs_head = QHBoxLayout()
        docs_title = QLabel("DOCUMENTOS VINCULADOS AO PROJETO")
        docs_title.setObjectName("section")
        docs_head.addWidget(docs_title)
        docs_head.addStretch()
        self.pdf_previous = QPushButton("◀ Página")
        self.pdf_previous.clicked.connect(self._pdf_previous)
        self.pdf_next = QPushButton("Página ▶")
        self.pdf_next.clicked.connect(self._pdf_next)
        self.pdf_page_label = QLabel("")
        docs_head.addWidget(self.pdf_previous)
        docs_head.addWidget(self.pdf_page_label)
        docs_head.addWidget(self.pdf_next)
        open_button = QPushButton("Abrir arquivo")
        open_button.clicked.connect(self._open_document)
        docs_head.addWidget(open_button)
        scan_button = QPushButton("Analisar arquivos")
        scan_button.clicked.connect(self._scan_documents)
        docs_head.addWidget(scan_button)
        refresh_button = QPushButton("Atualizar")
        refresh_button.clicked.connect(self._refresh_documents)
        docs_head.addWidget(refresh_button)
        docs_layout.addLayout(docs_head)

        docs_body = QSplitter(Qt.Orientation.Horizontal)
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
        docs_body.addWidget(self.document_tree)
        docs_body.addWidget(self.preview_stack)
        docs_body.setSizes([320, 1000])
        docs_layout.addWidget(docs_body, 1)

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(workspace)
        vertical.addWidget(docs_panel)
        vertical.setChildrenCollapsible(True)
        vertical.setCollapsible(0, False)
        vertical.setSizes([690, 170])
        outer.addWidget(vertical, 1)

        self.status = QLabel("Pronto")
        self.status.setObjectName("muted")
        outer.addWidget(self.status)
        self.setCentralWidget(root)
        self.setStyleSheet(DASHBOARD_STYLE)
        self.statusBar().showMessage(
            "Banco local preservado · alterações salvas automaticamente"
        )

    def _refresh_grid(self, *args):
        super()._refresh_grid(*args)
        self._refresh_dashboard()

    @staticmethod
    def _format_stat(value):
        if value is None:
            return "—"
        return f"{value:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def _refresh_dashboard(self):
        records = list(getattr(self, "_records", []) or [])
        columns = list(getattr(self, "columns", []) or [])
        numeric_columns = [
            column for column in columns
            if column.get("data_type") in {"integer", "decimal"}
        ]
        total = 0
        if self.table_id is not None:
            try:
                total = len(self.store.list_records(self.table_id))
            except Exception:
                total = len(records)
        self.indicators_headline.setText(f"{len(records)} obras encontradas")
        active = (
            len(self._filters) + len(self._conditions)
            + len(self._technical_criteria)
            + int(bool(self.search_input.text().strip()))
        )
        self.indicators_detail.setText(
            f"{active} filtro(s)/pesquisa(s) ativo(s) · "
            f"Base original: {total} registro(s) · "
            f"{len(numeric_columns)} campo(s) numérico(s)"
        )
        self.grid_count.setText(f"{len(records)} de {total} registros")
        self.filter_state_label.setText(
            f"{active} filtro(s)/pesquisa(s) ativo(s)"
            if active else "Nenhum filtro ativo"
        )

        summaries = summarize_numeric_columns(numeric_columns, records)
        self.indicators_table.setSortingEnabled(False)
        self.indicators_table.setRowCount(len(numeric_columns))
        for row, column in enumerate(numeric_columns):
            summary = summaries[column["name"]]
            results = [
                column["name"], str(summary["count"]),
                self._format_stat(summary["mean"]),
                self._format_stat(summary["median"]),
                self._format_stat(summary["minimum"]),
                self._format_stat(summary["maximum"]),
            ]
            for col, value in enumerate(results):
                item = QTableWidgetItem(value)
                if col:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.indicators_table.setItem(row, col, item)
        self.indicators_table.setSortingEnabled(True)

    def _update_selected_properties(self, current_row, _current_column, *_):
        if current_row < 0 or current_row >= len(self._records):
            self.properties_view.clear()
            return
        record = self._records[current_row]
        lines = [f"ID do registro: {record.get('id', '—')}", ""]
        for column in self.columns:
            name = column.get("name", "")
            value = record.get("values", {}).get(name)
            lines.append(f"{name}: {'—' if value is None else value}")
        self.properties_view.setPlainText("\n".join(lines))
