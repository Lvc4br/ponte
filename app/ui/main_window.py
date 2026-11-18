from pathlib import Path
import hashlib
import threading

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPushButton, QProgressDialog, QSplitter, QTabBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget,
)

from app.core.analytics import RATE_FIELDS, summarize_rates
from app.core.matching import missing_criteria_fields
from app.core.models import NumericRange, SearchCriteria
from app.core.validation import format_display_value, parse_input_number
from app.data.excel_importer import read_excel
from app.data.repository import SQLRepository
from app.data.backup_manager import DatabaseBackupManager
from app.services.search_service import SearchService
from app.documents.scanner import DocumentScanner
from app.documents.index import DocumentIndex
from app.ui.document_scan_dialog import DocumentScanDialog
from app.ui.document_library_dialog import DocumentLibraryDialog
from app.workspace.store import WorkspaceStore
from app.ui.workspace_dialog import WorkspaceDialog


RATE_LABELS = {
    "em_m3_m2": "Concreto (em_m3_m2)",
    "Paf_kg_m2": "Paf_kg_m2",
    "Pap_kg_m2": "Pap_kg_m2",
    "Af_m2_m2": "Af_m2_m2",
}

APP_STYLE = """
QMainWindow, QWidget#workspace { background: #202328; color: #e5e7eb; }
QFrame#topbar, QFrame#sidebar, QFrame#properties, QFrame#panel {
    background: #2a2e35; border: 1px solid #383e47; border-radius: 6px;
}
QLabel { color: #d8dce2; }
QLabel#brand { color: #f1a34a; font-size: 17px; font-weight: 800; letter-spacing: 1px; }
QLabel#pageTitle { color: #f4f5f7; font-size: 23px; font-weight: 700; }
QLabel#muted { line-height: 1.25; }
QPushButton { min-height: 18px; }
QPushButton#nav { min-height: 20px; }
QLabel#muted { color: #9ba3af; }
QLabel#sectionTitle { color: #f0a34a; font-size: 11px; font-weight: 800; }
QLineEdit {
    background: #1d2025; color: #f0f2f5; border: 1px solid #454c57;
    border-radius: 4px; padding: 7px; selection-background-color: #bd762f;
}
QLineEdit:focus { border: 1px solid #e39a43; }
QPushButton, QToolButton {
    background: #383e47; color: #e8eaed; border: 1px solid #4a515c;
    border-radius: 4px; padding: 7px 10px;
}
QPushButton:hover, QToolButton:hover { background: #454d58; border-color: #d58c3d; }
QPushButton#primary { background: #b96f2d; color: #fff; border: 1px solid #d48b43; font-weight: 700; }
QPushButton#primary:hover { background: #d08337; }
QPushButton#nav { text-align: left; padding: 10px; background: transparent; border: 0; }
QPushButton#nav:checked { background: #414751; color: #f4b15f; border-left: 3px solid #e49a43; }
QTabWidget::pane { border: 1px solid #3b424c; background: #25292f; }
QTabBar::tab {
    background: #2c3138; color: #aeb5bf; padding: 9px 16px;
    border: 1px solid #3a414b; border-bottom: 0; margin-right: 2px;
}
QTabBar::tab:selected { background: #25292f; color: #f2ae5b; border-top: 2px solid #e49a43; }
QTabBar#datasetTabs { background: #25292f; }
QTabBar#datasetTabs::tab { padding: 8px 14px; min-width: 90px; }
QTabBar#datasetTabs::tab:selected { background: #343a43; }
QTableWidget::item { padding: 3px 5px; }
QTableWidget::item:selected { background: #59432f; }
QTableWidget {
    background: #22262c; alternate-background-color: #292e35;
    color: #e1e5e9; gridline-color: #3b424c;
    border: 1px solid #3b424c; selection-background-color: #57432f;
    selection-color: #fff3e3;
}
QHeaderView::section {
    background: #343a43; color: #e6e9ed; padding: 7px;
    border: 0; border-right: 1px solid #464d58; border-bottom: 1px solid #4b535e;
    font-weight: 700;
}
QTableCornerButton::section { background: #343a43; border: 0; }
QScrollBar:vertical { background: #25292f; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #505864; min-height: 24px; border-radius: 5px; }
QScrollBar:horizontal { background: #25292f; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #505864; min-width: 24px; border-radius: 5px; }
QStatusBar { background: #191c20; color: #aeb5bf; border-top: 1px solid #3b424c; }
QMenu { background: #2b3037; color: #e5e7eb; border: 1px solid #454c57; }
QMenu::item:selected { background: #57432f; }
"""


def _sha256_file(path):
    """Calculate a streaming SHA-256 fingerprint without loading the file in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pt_number(value):
    if value is None:
        return "—"
    return f"{value:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")


class DocumentScanWorker(QThread):
    completed = Signal(object)
    progress = Signal(int, int, str)

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        results = DocumentScanner().scan_many(
            self.paths,
            progress_callback=self.progress.emit,
            cancel_event=self.cancel_event,
        )
        self.completed.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PONTE | Gerenciador Universal de Dados e Documentos")
        self.resize(1540, 920)
        self.setMinimumSize(1120, 700)
        self.repo = SQLRepository()
        self.document_index = DocumentIndex()
        self.workspace_store = WorkspaceStore()
        self.service = SearchService()
        self.results = []
        self._records_by_id = {}
        self._active_dataset = '__all__'
        self._build()
        self.load_sql()

    def _build(self):
        workspace = QWidget()
        workspace.setObjectName("workspace")
        root = QVBoxLayout(workspace)
        root.setContentsMargins(10, 10, 10, 6)
        root.setSpacing(8)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        top = QHBoxLayout(topbar)
        top.setContentsMargins(14, 8, 14, 8)
        brand = QLabel("PONTE")
        brand.setObjectName("brand")
        top.addWidget(brand)
        divider = QLabel("/")
        divider.setObjectName("muted")
        top.addWidget(divider)
        subtitle = QLabel("GERENCIADOR UNIVERSAL  ·  DADOS E DOCUMENTOS")
        subtitle.setObjectName("muted")
        top.addWidget(subtitle)
        top.addStretch()
        self.workspace_status = QLabel("BASE LOCAL")
        self.workspace_status.setObjectName("muted")
        top.addWidget(self.workspace_status)
        self.actions_button = QToolButton()
        self.actions_button.setText("⋮")
        self.actions_button.setToolTip("Mais ações")
        self.actions_button.setAccessibleName("Mais ações")
        self.actions_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        actions_menu = QMenu(self.actions_button)
        actions_menu.addAction("Recarregar fonte SQL", self.load_sql)
        actions_menu.addAction("Importar planilha Excel (base legada)", self.import_excel)
        actions_menu.addAction("Analisar documentos...", self.scan_documents)
        actions_menu.addAction("Analisar pasta inteira...", self.scan_document_folder)
        actions_menu.addAction("Biblioteca documental", self.open_document_library)
        actions_menu.addAction("Espaço de dados (projetos e tabelas)", self.open_workspace)
        actions_menu.addSeparator()
        actions_menu.addAction("Criar backup do banco...", self.create_database_backup)
        actions_menu.addAction("Verificar backup...", self.verify_database_backup)
        actions_menu.addAction("Restaurar backup...", self.restore_database_backup)
        actions_menu.addSeparator()
        actions_menu.addAction("Excluir registros selecionados", self.delete_selected)
        self.actions_button.setMenu(actions_menu)
        top.addWidget(self.actions_button)
        root.addWidget(topbar)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(175)
        sidebar.setMaximumWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(10, 14, 10, 12)
        side.setSpacing(7)
        section = QLabel("NAVEGAÇÃO")
        section.setObjectName("sectionTitle")
        side.addWidget(section)

        self.nav_data = QPushButton("▦   Base legada")
        self.nav_data.setObjectName("nav")
        self.nav_data.setCheckable(True)
        self.nav_data.setChecked(True)
        self.nav_indicators = QPushButton("▥   Indicadores")
        self.nav_indicators.setObjectName("nav")
        self.nav_indicators.setCheckable(True)
        self.nav_data.clicked.connect(lambda: self._switch_tab(0))
        self.nav_indicators.clicked.connect(lambda: self._switch_tab(1))
        side.addWidget(self.nav_data)
        side.addWidget(self.nav_indicators)
        self.nav_workspace = QPushButton("▦   Espaço de dados")
        self.nav_workspace.setObjectName("nav")
        self.nav_workspace.clicked.connect(self.open_workspace)
        self.nav_documents = QPushButton("▧   Biblioteca documental")
        self.nav_documents.setObjectName("nav")
        self.nav_documents.clicked.connect(self.open_document_library)
        side.addWidget(self.nav_workspace)
        side.addWidget(self.nav_documents)

        side.addSpacing(12)
        filter_title = QLabel("FILTROS DE CONSULTA")
        filter_title.setObjectName("sectionTitle")
        side.addWidget(filter_title)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Tipo de obra")
        side.addWidget(self.type_input)
        self.fields = {}
        for key, label in [
            ("width", "Largura (m)"),
            ("span", "Vão (m)"),
            ("total_length", "Comprimento (m)"),
        ]:
            caption = QLabel(label)
            caption.setObjectName("muted")
            side.addWidget(caption)
            pair = QHBoxLayout()
            low, high = QLineEdit(), QLineEdit()
            low.setPlaceholderText("Mín.")
            high.setPlaceholderText("Máx.")
            pair.addWidget(low)
            pair.addWidget(high)
            side.addLayout(pair)
            self.fields[key] = (low, high)

        search_button = QPushButton("Aplicar filtros")
        search_button.setObjectName("primary")
        search_button.clicked.connect(self.search)
        clear_button = QPushButton("Limpar filtros")
        clear_button.clicked.connect(self.clear)
        side.addWidget(search_button)
        side.addWidget(clear_button)
        side.addStretch()

        help_label = QLabel(
            "DICA\nSelecione uma linha da planilha para consultar os campos "
            "da obra no painel de propriedades."
        )
        help_label.setObjectName("muted")
        help_label.setWordWrap(True)
        side.addWidget(help_label)
        body.addWidget(sidebar)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(4, 0, 4, 0)
        center_layout.setSpacing(10)

        page_header = QVBoxLayout()
        page_header.setSpacing(10)
        heading = QVBoxLayout()
        heading.setSpacing(3)
        self.page_title = QLabel("Base legada — Obras e pontes")
        self.page_title.setObjectName("pageTitle")
        heading.addWidget(self.page_title)
        page_subtitle = QLabel(
            "Conjunto de dados legado. Crie projetos de qualquer área no Espaço de dados."
        )
        page_subtitle.setObjectName("muted")
        page_subtitle.setWordWrap(True)
        heading.addWidget(page_subtitle)
        page_header.addLayout(heading)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(7)
        self.import_button = QPushButton("＋  Importar Excel")
        self.import_button.setObjectName("primary")
        self.import_button.clicked.connect(self.import_excel)
        self.scan_button = QPushButton("⌕  Analisar documentos")
        self.scan_button.clicked.connect(self.scan_documents)
        self.reload_button = QPushButton("↻  Atualizar")
        self.reload_button.clicked.connect(self.load_sql)
        self.delete_button = QPushButton("Excluir selecionados")
        self.delete_button.clicked.connect(self.delete_selected)
        actions_row.addWidget(self.import_button)
        actions_row.addWidget(self.scan_button)
        actions_row.addWidget(self.reload_button)
        actions_row.addWidget(self.delete_button)
        actions_row.addStretch()
        page_header.addLayout(actions_row)
        center_layout.addLayout(page_header)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)

        data_page = QWidget()
        data_layout = QVBoxLayout(data_page)
        data_layout.setContentsMargins(10, 10, 10, 10)
        data_layout.setSpacing(8)
        grid_toolbar = QHBoxLayout()
        grid_label = QLabel("REGISTROS DA BASE LEGADA")
        grid_label.setObjectName("sectionTitle")
        grid_toolbar.addWidget(grid_label)
        grid_toolbar.addStretch()
        self.grid_count = QLabel("0 registros")
        self.grid_count.setObjectName("muted")
        grid_toolbar.addWidget(self.grid_count)
        data_layout.addLayout(grid_toolbar)

        self.dataset_tabs = QTabBar()
        self.dataset_tabs.setObjectName("datasetTabs")
        self.dataset_tabs.setExpanding(False)
        self.dataset_tabs.setMovable(False)
        self.dataset_tabs.setUsesScrollButtons(True)
        self.dataset_tabs.currentChanged.connect(self._on_dataset_changed)
        data_layout.addWidget(self.dataset_tabs)

        self.table = QTableWidget()
        self.table.setObjectName("recordsGrid")
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(False)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(27)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setDefaultSectionSize(125)
        self.table.horizontalHeader().setMinimumSectionSize(75)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._update_properties)
        self.table.currentCellChanged.connect(
            lambda *_: self._update_properties()
        )
        data_layout.addWidget(self.table, 1)
        self.tabs.addTab(data_page, "Planilha")

        indicators_page = QWidget()
        indicators_layout = QVBoxLayout(indicators_page)
        indicators_layout.setContentsMargins(12, 12, 12, 12)
        indicators_layout.setSpacing(10)
        self.summary_headline = QLabel("Carregue a base para consultar.")
        self.summary_headline.setObjectName("pageTitle")
        self.summary_headline.setWordWrap(True)
        indicators_layout.addWidget(self.summary_headline)
        self.summary_detail = QLabel("")
        self.summary_detail.setObjectName("muted")
        self.summary_detail.setWordWrap(True)
        indicators_layout.addWidget(self.summary_detail)
        self.rate_table = QTableWidget(0, 7)
        self.rate_table.setHorizontalHeaderLabels([
            "Indicador (coluna de origem)", "Valores válidos", "Cobertura",
            "Média", "Mediana", "Mínimo", "Máximo",
        ])
        self.rate_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rate_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rate_table.setAlternatingRowColors(True)
        self.rate_table.verticalHeader().setVisible(False)
        self.rate_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.rate_table.horizontalHeader().setStretchLastSection(True)
        indicators_layout.addWidget(self.rate_table, 1)
        note = QLabel(
            "Estatísticas descritivas por registro, não necessariamente por obra única. "
            "Valores ausentes e textos não numéricos não entram no cálculo do indicador. "
            "A interpretação técnica de Paf, Pap e Af depende da documentação da fonte."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        indicators_layout.addWidget(note)
        self.tabs.addTab(indicators_page, "Indicadores")
        center_layout.addWidget(self.tabs, 1)
        body.addWidget(center)

        properties = QFrame()
        properties.setObjectName("properties")
        properties.setMinimumWidth(205)
        properties.setMaximumWidth(255)
        props = QVBoxLayout(properties)
        props.setContentsMargins(12, 14, 12, 12)
        props.setSpacing(8)
        props_title = QLabel("PROPRIEDADES")
        props_title.setObjectName("sectionTitle")
        props.addWidget(props_title)
        self.property_heading = QLabel("Nenhuma obra selecionada")
        self.property_heading.setStyleSheet("font-size:15px;font-weight:700;color:#f2f3f5")
        self.property_heading.setWordWrap(True)
        props.addWidget(self.property_heading)
        self.property_subtitle = QLabel("Selecione uma linha na planilha.")
        self.property_subtitle.setObjectName("muted")
        self.property_subtitle.setWordWrap(True)
        props.addWidget(self.property_subtitle)
        self.property_form = QFormLayout()
        self.property_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.property_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.property_form.setVerticalSpacing(8)
        props.addLayout(self.property_form, 1)
        self.property_values = []
        self.clear_properties()

        body.addWidget(properties)
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        body.setStretchFactor(2, 0)
        body.setSizes([185, 850, 225])
        root.addWidget(body, 1)

        self.setCentralWidget(workspace)
        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("Inicializando workspace...")
        self.setStyleSheet(APP_STYLE)

    def _switch_tab(self, index):
        self.tabs.setCurrentIndex(index)

    def _dataset_key(self, record):
        if not record.source_file:
            return "__base__"
        return f"{record.source_file}::{record.source_sheet or 'Planilha'}"

    def _dataset_records(self, key):
        if key == "__all__":
            return list(self.repo.records)
        if key == "__base__":
            return [record for record in self.repo.records if not record.source_file]
        return [record for record in self.repo.records if self._dataset_key(record) == key]

    def _refresh_dataset_navigation(self, selected_key=None):
        selected_key = selected_key or self._active_dataset
        entries = [("__all__", "Todas")]
        if any(not record.source_file for record in self.repo.records):
            entries.append(("__base__", "Base principal"))
        imported = {}
        for record in self.repo.records:
            if record.source_file:
                key = self._dataset_key(record)
                imported[key] = (record.source_file, record.source_sheet or "Planilha")
        for key, (file_name, sheet_name) in sorted(imported.items(), key=lambda item: item[1]):
            entries.append((key, f"{Path(file_name).stem} · {sheet_name}"))
        self.dataset_tabs.blockSignals(True)
        while self.dataset_tabs.count():
            self.dataset_tabs.removeTab(0)
        selected_index = 0
        for index, (key, label) in enumerate(entries):
            self.dataset_tabs.addTab(label)
            self.dataset_tabs.setTabData(index, key)
            if key == selected_key:
                selected_index = index
        self.dataset_tabs.setCurrentIndex(selected_index)
        self.dataset_tabs.blockSignals(False)
        self._active_dataset = entries[selected_index][0]
        self.dataset_tabs.setToolTip("Navegue entre a base principal e cada planilha importada.")

    def _on_dataset_changed(self, index):
        if index < 0:
            return
        key = self.dataset_tabs.tabData(index)
        if not key:
            return
        self._active_dataset = key
        records = self._dataset_records(key)
        self.results = records
        self.show_records(records)
        self.statusBar().showMessage(f"{self.dataset_tabs.tabText(index)}  |  {len(records)} registros")

    def _on_tab_changed(self, index):
        self.nav_data.setChecked(index == 0)
        self.nav_indicators.setChecked(index == 1)
        self.page_title.setText("Dados das obras" if index == 0 else "Indicadores das obras")

    def clear_properties(self):
        while self.property_form.rowCount():
            self.property_form.removeRow(0)
        self.property_values = []
        self.property_heading.setText("Nenhuma obra selecionada")
        self.property_subtitle.setText("Selecione uma linha na planilha.")

    def _update_properties(self):
        row = self.table.currentRow()
        if row < 0 or self.table.columnCount() == 0:
            self.clear_properties()
            return
        first = self.table.item(row, 0)
        record_id = first.data(Qt.ItemDataRole.UserRole) if first else None
        record = self._records_by_id.get(record_id)
        if record is None:
            self.clear_properties()
            return
        self.clear_properties()
        values = record.values
        title = next(
            (values.get(key) for key in ("obra", "Obra", "nome", "Nome", "id_obra")
             if values.get(key) not in (None, "")),
            f"Registro {record.source_row}",
        )
        self.property_heading.setText(str(title))
        self.property_subtitle.setText(f"ID local: {record.source_row}")
        for key, value in values.items():
            label = QLabel(str(key))
            label.setObjectName("muted")
            content = QLabel(format_display_value(value))
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.property_form.addRow(label, content)
            self.property_values.append((label, content))

    def load_sql(self):
        try:
            records = self.repo.load()
            self.results = records
            self._refresh_dataset_navigation("__all__")
            self.show_records(self._dataset_records(self._active_dataset))
            source_label = (
                Path(self.repo.source).name if self.repo.source
                else "Base local salva"
            )
            self.workspace_status.setText("BASE LOCAL  ·  CONECTADA")
            self.statusBar().showMessage(
                f"{source_label}  |  {len(records)} registros carregados"
            )
        except Exception as exc:
            self.results = self.repo.records
            self._refresh_dataset_navigation("__all__")
            self.show_records(self._dataset_records(self._active_dataset))
            self.workspace_status.setText("BASE LOCAL  ·  ATENÇÃO")
            self.statusBar().showMessage("Não foi possível carregar a fonte SQL")
            QMessageBox.warning(
                self, "Não foi possível carregar a base SQL", str(exc)
            )

    def open_document_library(self):
        dialog = DocumentLibraryDialog(self.document_index, self)
        dialog.exec()

    def open_workspace(self):
        dialog = WorkspaceDialog(self.workspace_store, self.document_index, self)
        dialog.exec()

    def create_database_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Criar backup do banco", "PONTE-backup.sqlite3",
            "Banco SQLite (*.sqlite3)"
        )
        if not path:
            return
        if not path.lower().endswith(".sqlite3"):
            path += ".sqlite3"
        try:
            result = DatabaseBackupManager(self.workspace_store.path).create_backup(path)
            QMessageBox.information(
                self, "Backup concluído",
                f"Backup verificado e criado.\n\nArquivo: {result['path']}\n"
                f"Tamanho: {result['size_bytes']:,} bytes\nSHA-256: {result['sha256']}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Falha no backup", str(exc))

    def verify_database_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Verificar backup", "", "Banco SQLite (*.sqlite3)"
        )
        if not path:
            return
        try:
            result = DatabaseBackupManager(self.workspace_store.path).verify_backup(path)
            QMessageBox.information(
                self, "Backup íntegro",
                f"Integridade SQLite: {result['integrity']}\n"
                f"Tabelas: {result['table_count']}\n"
                f"Tamanho: {result['size_bytes']:,} bytes\nSHA-256: {result['sha256']}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Backup inválido", str(exc))

    def restore_database_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar backup para restauração", "", "Banco SQLite (*.sqlite3)"
        )
        if not path:
            return
        answer = QMessageBox.warning(
            self, "Confirmar restauração",
            "A restauração substituirá o banco local atual. Um backup de segurança "
            "do banco atual será criado automaticamente. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            result = DatabaseBackupManager(self.workspace_store.path).restore(path)
            safety = result["safety_backup"]["path"] if result["safety_backup"] else "não necessário"
            QMessageBox.information(
                self, "Restauração concluída",
                f"Banco restaurado e verificado.\nBackup de segurança: {safety}\n\n"
                "Feche e abra novamente o PONTE para recarregar todos os dados."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Falha na restauração", str(exc))

    def scan_documents(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar documentos para análise",
            "",
            "Documentos suportados (*.pdf *.docx *.xlsx *.xlsm *.xls *.pptx *.csv *.txt *.md *.json *.xml *.dxf *.ifc *.png *.jpg *.jpeg *.tif *.tiff *.bmp);;Todos os arquivos (*.*)",
        )
        if paths:
            self._start_document_scan(paths)

    def scan_document_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta para varredura recursiva"
        )
        if folder:
            self._start_document_scan([folder])

    def _start_document_scan(self, paths):
        self.scan_progress = QProgressDialog(
            "Preparando a análise documental...",
            "Cancelar", 0, 0, self,
        )
        self.scan_progress.setWindowTitle("Análise documental")
        self.scan_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.scan_progress.setMinimumDuration(0)
        self.scan_progress.show()
        self.scan_worker = DocumentScanWorker(paths, self)
        self.scan_worker.progress.connect(self._update_document_progress)
        self.scan_worker.completed.connect(self._show_document_scan_results)
        self.scan_progress.canceled.connect(self.scan_worker.cancel)
        self.scan_worker.start()

    def _update_document_progress(self, current, total, file_name):
        if total:
            self.scan_progress.setRange(0, total)
            self.scan_progress.setValue(current)
            self.scan_progress.setLabelText(
                f"Analisando {file_name or 'documentos'} ({current}/{total})"
            )
        else:
            self.scan_progress.setLabelText("Nenhum arquivo encontrado na seleção.")

    def _show_document_scan_results(self, results):
        cancelled = self.scan_worker.cancel_event.is_set()
        self.scan_progress.close()
        self.last_document_scan_results = results
        try:
            for result in results:
                if result.sha256:
                    self.document_index.index_result(result)
        except Exception as exc:
            QMessageBox.warning(
                self, "Catálogo documental",
                f"Os arquivos foram analisados, mas houve falha ao salvar o catálogo local: {exc}",
            )
        dialog = DocumentScanDialog(results, self)
        dialog.exec()
        state = "cancelada" if cancelled else "concluída"
        self.statusBar().showMessage(
            f"Análise {state}: {len(results)} arquivo(s) processado(s)."
        )

    def import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar planilha Excel", "",
            "Planilhas Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            file_hash = _sha256_file(path)
            file_name = Path(path).name
            from openpyxl import load_workbook
            workbook = load_workbook(path, read_only=True, data_only=False)
            try:
                sheets = workbook.sheetnames
            finally:
                workbook.close()
            sheet, accepted = QInputDialog.getItem(
                self, "Selecionar aba", "Aba para importar:", sheets, 0, False
            )
            if not accepted:
                return
            sheet_fingerprint = hashlib.sha256(
                f"{file_hash}:{sheet}".encode("utf-8")
            ).hexdigest()
            if self.repo.store.has_imported_file(sheet_fingerprint):
                QMessageBox.warning(
                    self, "Planilha já importada",
                    f"A aba '{sheet}' do arquivo '{file_name}' já foi importada.\n\n"
                    "A inclusão foi bloqueada para evitar registros duplicados. "
                    "Renomear o arquivo não altera essa verificação."
                )
                return
            incoming = read_excel(path, sheet)
            sample = incoming[:5]
            preview = "\n".join(
                " • " + ", ".join(
                    f"{key}: {format_display_value(value)}"
                    for key, value in record.values.items()
                )
                for record in sample
            )
            more = (
                f"\n... e mais {len(incoming) - len(sample)} registro(s)"
                if len(incoming) > len(sample) else ""
            )
            answer = QMessageBox.question(
                self, "Confirmar inclusão",
                f"Arquivo: {file_name}\nAba: {sheet}\n"
                f"Novos registros: {len(incoming)}\n\n"
                f"Prévia das primeiras linhas:\n{preview}{more}\n\n"
                "Os registros serão adicionados à base atual. "
                "A combinação do arquivo e da aba será identificada por SHA-256 para impedir duplicidade.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            count = self.repo.add_excel_records(incoming, sheet_fingerprint, file_name, sheet)
            self.results = self.repo.records
            self._refresh_dataset_navigation(f"{file_name}::{sheet}")
            self.show_records(self._dataset_records(self._active_dataset))
            self.statusBar().showMessage(
                f"{count} registros adicionados  |  {len(self.repo.records)} ativos"
            )
            QMessageBox.information(
                self, "Importação concluída",
                f"{count} registro(s) adicionados. Esta aba foi registrada e não poderá "
                "ser importada novamente nesta base."
            )
        except Exception as exc:
            QMessageBox.warning(self, "Falha na importação", str(exc))

    def delete_selected(self):
        selected_rows = sorted({
            index.row() for index in self.table.selectionModel().selectedRows()
        })
        if not selected_rows:
            QMessageBox.information(
                self, "Nenhum registro selecionado",
                "Selecione uma ou mais linhas na planilha antes de excluir."
            )
            return
        ids = []
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item is not None:
                record_id = item.data(Qt.ItemDataRole.UserRole)
                if record_id is not None:
                    ids.append(record_id)
        if not ids:
            QMessageBox.warning(
                self, "Não foi possível excluir",
                "Não foi possível identificar os registros selecionados."
            )
            return
        answer = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Excluir permanentemente {len(ids)} registro(s) selecionado(s) "
            "da base local? A fonte SQL original não será alterada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repo.store.backup()
            deleted = self.repo.delete_records(ids)
            self.results = self.repo.records
            self._refresh_dataset_navigation(self._active_dataset)
            self.show_records(self._dataset_records(self._active_dataset))
            self.statusBar().showMessage(
                f"{deleted} registros excluídos  |  {len(self.repo.records)} ativos"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao excluir registros", str(exc))

    def criteria(self):
        data = {}
        labels = {
            "width": "Largura",
            "span": "Vão",
            "total_length": "Comprimento total",
        }
        for key, (low, high) in self.fields.items():
            minimum = parse_input_number(low.text(), f"{labels[key]} (mínimo)")
            maximum = parse_input_number(high.text(), f"{labels[key]} (máximo)")
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(
                    f"{labels[key]}: o valor mínimo não pode ser maior que o máximo."
                )
            data[key] = (
                NumericRange(
                    minimum if minimum is not None else float("-inf"),
                    maximum if maximum is not None else float("inf"),
                )
                if minimum is not None or maximum is not None else None
            )
        type_value = self.type_input.text().strip() or None
        return SearchCriteria(**data, type_obra=type_value)

    def search(self):
        active_records = self._dataset_records(self._active_dataset)
        if not active_records:
            QMessageBox.information(
                self, "Base necessária",
                "Coloque database/ponte.sql na pasta do aplicativo e cadastre os dados autorizados."
            )
            return
        try:
            criteria = self.criteria()
            self.results = self.service.search(active_records, criteria)
            self.show_records(self.results, criteria)
            self.statusBar().showMessage(
                f"{len(self.results)} de {len(self.repo.records)} registros correspondem aos filtros"
            )
            self.tabs.setCurrentIndex(0)
        except ValueError as exc:
            QMessageBox.warning(self, "Filtros inválidos", str(exc))
        except Exception as exc:
            QMessageBox.critical(
                self, "Falha na pesquisa",
                f"Não foi possível concluir a pesquisa.\n\nDetalhes: {exc}"
            )

    def clear(self):
        self.type_input.clear()
        for low, high in self.fields.values():
            low.clear()
            high.clear()
        self.results = self._dataset_records(self._active_dataset)
        self.show_records(self.results)
        self.statusBar().showMessage(f"{len(self.results)} registros carregados")

    def _show_summary(self, records, criteria=None):
        source_count = len(self._dataset_records(self._active_dataset))
        result_count = len(records)
        if criteria is None:
            self.summary_headline.setText(
                f"Base de obras: {source_count} registros disponíveis."
            )
            self.summary_detail.setText(
                "Sem filtros ativos. As estatísticas consideram todos os registros carregados."
            )
        else:
            uncertain = sum(
                bool(missing_criteria_fields(record, criteria))
                for record in records
            )
            verified = result_count - uncertain
            rejected = max(0, source_count - result_count)
            self.summary_headline.setText(
                f"{result_count} registros retornados de {source_count} registros da base."
            )
            self.summary_detail.setText(
                f"Compatibilidade verificável: {verified}  |  "
                f"Dados insuficientes: {uncertain}  |  "
                f"Não retornados por divergência: {rejected}.\n"
                "Registros incompletos permanecem disponíveis para conferência."
            )
        summaries = summarize_rates(records)
        self.rate_table.setSortingEnabled(False)
        self.rate_table.setRowCount(len(RATE_FIELDS))
        for row, field in enumerate(RATE_FIELDS):
            item = summaries[field]
            count = item["count"]
            coverage = (100 * count / result_count) if result_count else 0
            values = [
                RATE_LABELS.get(field, field), str(count),
                f"{coverage:.1f}%".replace(".", ","),
                _pt_number(item["mean"]), _pt_number(item["median"]),
                _pt_number(item["minimum"]), _pt_number(item["maximum"]),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column > 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rate_table.setItem(row, column, cell)
        self.rate_table.setSortingEnabled(True)

    def show_records(self, records, criteria=None):
        self._show_summary(records, criteria)
        self._records_by_id = {record.source_row: record for record in records}
        columns = list(dict.fromkeys(
            key for record in records for key in record.values
        ))
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setRowCount(len(records))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        for row_index, record in enumerate(records):
            for column_index, key in enumerate(columns):
                value = format_display_value(record.get(key))
                cell = QTableWidgetItem(value)
                if column_index == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, record.source_row)
                self.table.setItem(row_index, column_index, cell)
        self.table.setSortingEnabled(True)
        self.grid_count.setText(f"{len(records)} registros")
        self.clear_properties()
