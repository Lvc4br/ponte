"""PONTE v2 application shell aligned with the approved desktop design system.

The shell provides persistent module navigation and a light operational workspace.
Only values backed by local stores are shown as metrics; unavailable indicators are
explicitly marked as not yet calculated.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QScrollArea, QComboBox, QLineEdit,
    QFileDialog, QTabWidget,
)

from app.documents.index import DocumentIndex
from app.documents.scanner import DocumentScanner
from app.workspace.store import WorkspaceStore
from app.workspace.exchange import SpreadsheetExchange
from app.data.dataset_store import DEFAULT_STORE, DatasetStore
from app.core.bridge_formatters import bridge_span_text


NAV_ITEMS = [
    ("Visão geral", "⌂"),
    ("Projetos e obras", "▦"),
    ("Pontes e OAEs", "▤"),
    ("Importar dados", "⇧"),
    ("Análise de engenharia", "⌕"),
    ("Documentos", "▧"),
    ("Relatórios", "▥"),
]


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, note: str, accent: str = "#2f80b7"):
        super().__init__()
        self.setObjectName("metricCard")
        self.setStyleSheet(
            f"QFrame#metricCard {{ background:#ffffff; border:1px solid #e1e7ed; "
            f"border-left:4px solid {accent}; border-radius:8px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        label = QLabel(title)
        label.setObjectName("muted")
        number = QLabel(value)
        number.setObjectName("metricValue")
        foot = QLabel(note)
        foot.setObjectName("mutedSmall")
        foot.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(number)
        layout.addWidget(foot)


class Panel(QFrame):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("panel")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 15, 18, 17)
        self.body.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("panelTitle")
        self.body.addWidget(heading)
        if subtitle:
            detail = QLabel(subtitle)
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            self.body.addWidget(detail)


class FileDropFrame(QFrame):
    """Drop target that forwards one supported local file to the import flow."""

    def __init__(self, on_file_dropped):
        super().__init__()
        self._on_file_dropped = on_file_dropped
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(url.isLocalFile() for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        supported = {".xlsx", ".xlsm", ".xls", ".xlsb", ".csv"}
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if Path(path).suffix.casefold() in supported:
                    self._on_file_dropped(path)
                    event.acceptProposedAction()
                    return
        event.ignore()


class PonteMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PONTE | Engenharia • Inteligência")
        self.resize(1440, 900)
        self.setMinimumSize(1120, 720)

        self.store = WorkspaceStore()
        self.documents = DocumentIndex()
        self.pages: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}

        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(13, 22, 13, 16)
        side.setSpacing(7)

        brand = QLabel("PONTE")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("ENGENHARIA • INTELIGÊNCIA")
        tagline.setObjectName("tagline")
        side.addWidget(tagline)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sideLine")
        side.addWidget(line)
        side.addSpacing(8)

        self.stack = QStackedWidget()
        for title, symbol in NAV_ITEMS:
            button = QPushButton(f"{symbol}   {title}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, name=title: self.navigate(name))
            side.addWidget(button)
            self.nav_buttons[title] = button

        side.addStretch(1)
        side_status = QLabel("WORKSPACE LOCAL\nDados armazenados neste dispositivo")
        side_status.setObjectName("workspaceNote")
        side_status.setWordWrap(True)
        side.addWidget(side_status)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 18, 28, 22)
        content_layout.setSpacing(18)

        top = QHBoxLayout()
        self.breadcrumb = QLabel("Ponte  /  Visão geral")
        self.breadcrumb.setObjectName("breadcrumb")
        top.addWidget(self.breadcrumb)
        top.addStretch()
        org = QLabel("EGT Engenharia   •   ▾")
        org.setObjectName("orgLabel")
        top.addWidget(org)
        content_layout.addLayout(top)

        self.page_title = QLabel("Painel operacional")
        self.page_title.setObjectName("pageTitle")
        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(self._stylesheet())

        self._build_pages()
        self.navigate("Visão geral")

    def _stylesheet(self) -> str:
        return """
        QWidget#root { background:#f3f6f9; color:#243447; font-family:'Segoe UI'; font-size:10pt; }
        QFrame#sidebar { background:#14283f; }
        QLabel#brand { color:#ffffff; font-size:25px; font-weight:800; letter-spacing:1px; }
        QLabel#tagline { color:#9fb1c4; font-size:8pt; }
        QFrame#sideLine { color:#33485e; background:#33485e; max-height:1px; }
        QPushButton#navButton { text-align:left; color:#c6d2df; background:transparent;
            border:0; border-radius:6px; padding:11px 10px; font-size:9pt; }
        QPushButton#navButton:hover { background:#203a56; color:#ffffff; }
        QPushButton#navButton:checked { background:#25435f; color:#ffffff; font-weight:700; }
        QLabel#workspaceNote { color:#91a5ba; font-size:8pt; border-top:1px solid #33485e; padding-top:14px; }
        QWidget#content { background:#f3f6f9; }
        QLabel#breadcrumb, QLabel#muted, QLabel#orgLabel { color:#748396; }
        QLabel#orgLabel { font-size:9pt; }
        QLabel#pageTitle { color:#1e3044; font-size:17pt; font-weight:700; }
        QLabel#sectionIntro { color:#66778a; font-size:10pt; }
        QLabel#metricValue { color:#26384b; font-size:24px; font-weight:750; padding:3px 0; }
        QLabel#mutedSmall { color:#8492a2; font-size:8pt; }
        QFrame#panel { background:#ffffff; border:1px solid #e1e7ed; border-radius:8px; }
        QLabel#panelTitle { color:#26384b; font-size:11pt; font-weight:700; }
        QPushButton#primaryAction { background:#287db5; color:#ffffff; border:0; border-radius:6px;
            padding:10px 15px; font-weight:650; }
        QPushButton#primaryAction:hover { background:#216b9c; }
        QPushButton#secondaryAction { background:#ffffff; color:#2d6f9f; border:1px solid #d7e0e8;
            border-radius:6px; padding:9px 13px; }
        QPushButton#secondaryAction:hover { background:#edf4f9; }
        QTableWidget { background:#ffffff; alternate-background-color:#f7f9fb; color:#2b3c4e;
            border:0; gridline-color:#e6ebf0; selection-background-color:#e5f0f8;
            selection-color:#20364a; }
        QHeaderView::section { background:#eaf0f5; color:#42566b; border:0;
            padding:9px 7px; font-weight:700; }
        """

    def _build_pages(self):
        self._add_page("Visão geral", self._overview_page())
        self._add_page("Projetos e obras", self._projects_page())
        self._add_page("Pontes e OAEs", self._bridges_page())
        self._add_page("Importar dados", self._import_page())
        self._add_page("Análise de engenharia", self._analysis_page())
        self._add_page("Documentos", self._documents_page())
        self._add_page("Relatórios", self._reports_page())

    def _add_page(self, name: str, page: QWidget):
        self.pages[name] = page
        self.stack.addWidget(page)

    def navigate(self, name: str):
        page = self.pages.get(name)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.page_title.setText({
            "Visão geral": "Painel operacional",
            "Projetos e obras": "Projetos e obras",
            "Pontes e OAEs": "Cadastro técnico de pontes e OAEs",
            "Importar dados": "Entrada e validação de planilhas",
            "Análise de engenharia": "Filtros e indicadores",
            "Documentos": "Biblioteca documental",
            "Relatórios": "Relatórios e exportações",
        }.get(name, name))
        self.breadcrumb.setText(f"Ponte  /  {name}")
        for title, button in self.nav_buttons.items():
            button.setChecked(title == name)

    def _metric_row(self, cards: list[MetricCard]) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        for card in cards:
            layout.addWidget(card, 1)
        return row

    def _overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        intro = QHBoxLayout()
        text = QVBoxLayout()
        heading = QLabel("Acompanhe seus dados de engenharia")
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        sub = QLabel("Resumo atualizado a partir dos registros locais do PONTE.")
        sub.setObjectName("sectionIntro")
        text.addWidget(heading)
        text.addWidget(sub)
        intro.addLayout(text)
        intro.addStretch()
        import_button = QPushButton("+  Importar tabela")
        import_button.setObjectName("primaryAction")
        import_button.clicked.connect(lambda: self.navigate("Importar dados"))
        intro.addWidget(import_button)
        layout.addLayout(intro)

        projects = self.store.list_projects()
        try:
            with sqlite3.connect(DEFAULT_STORE) as db:
                bridge_count = db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        except sqlite3.Error:
            bridge_count = 0
        layout.addWidget(self._metric_row([
            MetricCard("Projetos cadastrados", str(len(projects)), "Projetos registrados no workspace local"),
            MetricCard("Registros de origem", str(bridge_count), "Registros importados; ainda não equivalem a OAEs validadas", "#4d9b8a"),
            MetricCard("Dados pendentes", "Não apurado", "A fila de validação ainda não está integrada", "#c58b3e"),
            MetricCard("Conjuntos analisáveis", "Não apurado", "Compatibilidade técnica ainda não calculada", "#4d9b8a"),
        ]))

        middle = QHBoxLayout()
        activity = Panel("Atividade recente", "Movimentações registradas no workspace")
        empty = QLabel("Nenhuma atividade recente disponível. O histórico de auditoria ainda não está integrado.")
        empty.setObjectName("muted")
        empty.setWordWrap(True)
        activity.body.addWidget(empty)
        middle.addWidget(activity, 3)

        pending = Panel("Pendências de validação", "Priorize inconsistências antes de comparar")
        for label, detail in [
            ("Unidades não identificadas", "Não apurado"),
            ("Campos geométricos ausentes", "Não apurado"),
            ("Quantitativos duplicados", "Não apurado"),
            ("Origem não informada", "Não apurado"),
        ]:
            line = QHBoxLayout()
            item = QLabel("•  " + label)
            item.setStyleSheet("color:#46586b;")
            value = QLabel(detail)
            value.setObjectName("muted")
            line.addWidget(item)
            line.addStretch()
            line.addWidget(value)
            pending.body.addLayout(line)
        middle.addWidget(pending, 2)
        layout.addLayout(middle, 1)

        quick = Panel("Acesso rápido")
        shortcuts = QHBoxLayout()
        for title, detail, module in [
            ("Importar planilha", "XLSX, XLS ou CSV", "Importar dados"),
            ("Analisar dados", "Filtros e indicadores", "Análise de engenharia"),
            ("Consultar OAEs", "Cadastro e geometria", "Pontes e OAEs"),
            ("Gerar relatório", "Resultados e evidências", "Relatórios"),
        ]:
            card = QFrame()
            card.setStyleSheet("QFrame {background:#f7f9fb;border:1px solid #e4eaf0;border-radius:7px;}")
            box = QVBoxLayout(card)
            box.setContentsMargins(13, 12, 13, 12)
            name = QLabel(title)
            name.setStyleSheet("font-weight:700;color:#34485c;")
            desc = QLabel(detail)
            desc.setObjectName("mutedSmall")
            link = QPushButton("Abrir módulo →")
            link.setObjectName("secondaryAction")
            link.clicked.connect(lambda checked=False, target=module: self.navigate(target))
            box.addWidget(name)
            box.addWidget(desc)
            box.addStretch()
            box.addWidget(link)
            shortcuts.addWidget(card, 1)
        quick.body.addLayout(shortcuts)
        layout.addWidget(quick)
        return page

    def _projects_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(
            "Pesquise, filtre e acompanhe empreendimentos e contratos aos quais as OAEs estão vinculadas."
        )
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.project_rows = self.store.list_projects()
        cards = self._metric_row([
            MetricCard("Projetos cadastrados", str(len(self.project_rows)), "Registros no workspace local"),
            MetricCard("OAEs vinculadas", "Não apurado", "Relacionamento projeto–OAE ainda não integrado"),
            MetricCard("Em execução", "Não apurado", "Etapas não estruturadas no cadastro atual"),
            MetricCard("Com pendências", "Não apurado", "Validação de empreendimentos ainda não integrada"),
        ])
        layout.addWidget(cards)

        panel = Panel("Empreendimentos cadastrados", "Dados locais • campos não cadastrados permanecem como “Não informado”")
        toolbar = QHBoxLayout()
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("Buscar projeto, contrato ou responsável…")
        self.project_search.textChanged.connect(self._filter_project_rows)
        toolbar.addWidget(self.project_search, 2)
        self.project_status_filter = QComboBox()
        self.project_status_filter.addItem("Todos os status", "")
        self.project_responsible_filter = QComboBox()
        self.project_responsible_filter.addItem("Todos os responsáveis", "")
        statuses = set()
        responsibles = set()
        for project in self.project_rows:
            metadata = project.get("metadata") or {}
            status = metadata.get("status")
            responsible = metadata.get("responsible", metadata.get("responsavel"))
            if status:
                statuses.add(str(status))
            if responsible:
                responsibles.add(str(responsible))
        for value in sorted(statuses, key=str.casefold):
            self.project_status_filter.addItem(value, value)
        for value in sorted(responsibles, key=str.casefold):
            self.project_responsible_filter.addItem(value, value)
        self.project_status_filter.currentIndexChanged.connect(self._filter_project_rows)
        self.project_responsible_filter.currentIndexChanged.connect(self._filter_project_rows)
        toolbar.addWidget(self.project_status_filter)
        toolbar.addWidget(self.project_responsible_filter)
        create = QPushButton("+ Novo projeto")
        create.setObjectName("primaryAction")
        create.clicked.connect(self.create_project)
        toolbar.addWidget(create)
        panel.body.addLayout(toolbar)

        self.project_table = QTableWidget(len(self.project_rows), 6)
        self.project_table.setHorizontalHeaderLabels([
            "Projeto / contrato", "Local", "OAEs", "Etapa", "Responsável", "Status"
        ])
        self.project_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.project_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.project_table.verticalHeader().setVisible(False)
        self.project_table.horizontalHeader().setStretchLastSection(True)
        for row, project in enumerate(self.project_rows):
            metadata = project.get("metadata") or {}
            oae_count = metadata.get("oae_count", metadata.get("oaes"))
            values = [
                project.get("name"),
                metadata.get("location", metadata.get("local")),
                oae_count,
                metadata.get("stage", metadata.get("etapa")),
                metadata.get("responsible", metadata.get("responsavel")),
                metadata.get("status"),
            ]
            for col, value in enumerate(values):
                self.project_table.setItem(
                    row, col, QTableWidgetItem("Não informado" if value is None else str(value))
                )
        panel.body.addWidget(self.project_table, 1)
        layout.addWidget(panel, 1)
        return page

    def _filter_project_rows(self, *_):
        if not hasattr(self, "project_table"):
            return
        needle = self.project_search.text().strip().casefold()
        status = self.project_status_filter.currentData()
        responsible = self.project_responsible_filter.currentData()
        for row in range(self.project_table.rowCount()):
            values = [
                self.project_table.item(row, col).text()
                for col in range(self.project_table.columnCount())
                if self.project_table.item(row, col) is not None
            ]
            matches_text = not needle or needle in " ".join(values).casefold()
            matches_status = not status or values[5] == status
            matches_responsible = not responsible or values[4] == responsible
            self.project_table.setRowHidden(row, not (
                matches_text and matches_status and matches_responsible
            ))

    def create_project(self):
        name, accepted = QInputDialog.getText(self, "Novo projeto", "Nome do projeto:")
        if not accepted:
            return
        try:
            self.store.create_project(name)
            self.refresh_pages()
            self.navigate("Projetos e obras")
        except Exception as exc:
            QMessageBox.warning(self, "Não foi possível criar o projeto", str(exc))

    def _bridges_page(self) -> QWidget:
        """Show legacy bridge records without inventing or rewriting technical values."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel(
            "Consulte os registros de pontes e OAEs importados. Os valores permanecem "
            "vinculados à sua origem e não são tratados como validados."
        )
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        try:
            self.bridge_records = DatasetStore().load()
            load_error = None
        except Exception:
            self.bridge_records = []
            load_error = "Não foi possível carregar os registros locais. Verifique a base de dados."

        summary = self._metric_row([
            MetricCard("Registros de origem", str(len(self.bridge_records)),
                       "Linhas armazenadas no conjunto local"),
            MetricCard("Com tipologia", str(sum(bool(r.get("tipo_obra")) for r in self.bridge_records)),
                       "Campo informado na origem"),
            MetricCard("Com geometria", str(sum(
                r.get("compr_obra_m") is not None and r.get("largura_m") is not None
                for r in self.bridge_records
            )), "Comprimento e largura presentes"),
            MetricCard("Validação técnica", "Pendente",
                       "Cadastro e aprovação de engenharia ainda não integrados", "#c58b37"),
        ])
        layout.addWidget(summary)

        listing = Panel("Pontes e OAEs", "Registros importados • consulta da base local")
        self.bridge_search = QLineEdit()
        self.bridge_search.setPlaceholderText("Buscar por código, tipologia ou valor de origem…")
        self.bridge_search.textChanged.connect(self._filter_bridge_records)
        listing.body.addWidget(self.bridge_search)

        self.bridge_table = QTableWidget(len(self.bridge_records), 5)
        self.bridge_table.setHorizontalHeaderLabels([
            "Identificador", "Tipologia", "Comprimento (m)", "Largura (m)", "Vãos (m)"
        ])
        self.bridge_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bridge_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bridge_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bridge_table.verticalHeader().setVisible(False)
        self.bridge_table.horizontalHeader().setStretchLastSection(True)
        for row, record in enumerate(self.bridge_records):
            values = [
                record.get("obra", record.source_row),
                record.get("tipo_obra"),
                record.get("compr_obra_m"),
                record.get("largura_m"),
                self._bridge_span_text(record.values),
            ]
            for col, value in enumerate(values):
                self.bridge_table.setItem(
                    row, col, QTableWidgetItem("Não informado" if value is None else str(value))
                )
        self.bridge_table.itemSelectionChanged.connect(self._show_selected_bridge_record)
        listing.body.addWidget(self.bridge_table, 1)
        layout.addWidget(listing, 2)

        detail = Panel("Ficha técnica da OAE", "Consulta dos campos disponíveis no registro de origem • somente leitura")
        self.bridge_tabs = QTabWidget()
        self.bridge_tab_labels = {}
        empty_message = load_error or (
            "Nenhum registro legado de ponte/OAE foi encontrado nesta base. "
            "A importação genérica atual ainda não mapeia planilhas para o cadastro técnico de OAE."
            if not self.bridge_records else
            "Selecione uma linha acima. Campos ausentes serão exibidos como “Não informado”."
        )
        for key, title in [
            ("identification", "Identificação"),
            ("geometry", "Geometria"),
            ("quantities", "Materiais e quantitativos"),
            ("inspections", "Inspeções"),
            ("documents", "Documentos"),
            ("history", "Histórico"),
        ]:
            tab_label = QLabel(empty_message)
            tab_label.setWordWrap(True)
            tab_label.setObjectName("sectionIntro")
            tab_label.setContentsMargins(12, 12, 12, 12)
            self.bridge_tab_labels[key] = tab_label
            self.bridge_tabs.addTab(tab_label, title)
        detail.body.addWidget(self.bridge_tabs)
        layout.addWidget(detail, 1)

        if load_error:
            self.bridge_table.setEnabled(False)
        elif self.bridge_records:
            self.bridge_table.selectRow(0)
        return page

    @staticmethod
    def _bridge_span_text(values: dict) -> str:
        return bridge_span_text(values)

    def _filter_bridge_records(self, query: str):
        needle = query.strip().casefold()
        for row in range(self.bridge_table.rowCount()):
            text_value = " ".join(
                self.bridge_table.item(row, col).text()
                for col in range(self.bridge_table.columnCount())
                if self.bridge_table.item(row, col) is not None
            ).casefold()
            self.bridge_table.setRowHidden(row, bool(needle) and needle not in text_value)

    def _show_selected_bridge_record(self):
        selected = self.bridge_table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        record = self.bridge_records[row]
        fields = [
            ("Identificador", record.get("obra", record.source_row)),
            ("Tipologia", record.get("tipo_obra")),
            ("Seção", record.get("secao")),
            ("Largura do tabuleiro", record.get("largura_m"), "m"),
            ("Vão mínimo", record.get("vao_min_m", record.get("vão_min_m")), "m"),
            ("Vão máximo", record.get("vao_max_m", record.get("vão_max_m")), "m"),
            ("Comprimento total", record.get("compr_obra_m"), "m"),
            ("Ecm (campo da origem; unidade provisória)", record.get("em_m3_m2"), "m³/m²"),
            ("Paf", record.get("Paf_kg_m2"), "kg/m²"),
            ("Pap", record.get("Pap_kg_m2"), "kg/m²"),
            ("Af", record.get("Af_m2_m2"), "m²/m²"),
            ("anc_at_pas (campo original; significado a confirmar)", record.get("anc_at_pas")),
        ]
        parts = []
        for item in fields:
            label, value, *unit = item
            rendered = "Não informado" if value is None else str(value)
            if unit and value is not None:
                rendered = f"{rendered} {unit[0]}"
            parts.append(f"{label}: {rendered}")
        source = f"Origem: {record.source_file or 'base local'}"
        if record.source_sheet:
            source += f" • Aba: {record.source_sheet}"
        source += f" • Linha de origem: {record.source_row}"
        identity_fields = [
            ("Identificador", record.get("obra", record.source_row)),
            ("Nome da estrutura", record.get("nome", record.get("obra_nome"))),
            ("Projeto", record.get("projeto")),
            ("Tipologia", record.get("tipo_obra")),
            ("Município / UF", record.get("municipio")),
            ("Rodovia / km", record.get("rodovia")),
            ("Latitude", record.get("latitude")),
            ("Longitude", record.get("longitude")),
        ]
        geometry_fields = [
            ("Comprimento total", record.get("compr_obra_m"), "m"),
            ("Largura do tabuleiro", record.get("largura_m"), "m"),
            ("Vão mínimo", record.get("vao_min_m", record.get("vão_min_m")), "m"),
            ("Vão máximo", record.get("vao_max_m", record.get("vão_max_m")), "m"),
            ("Seção", record.get("secao")),
            ("Altura de viga/laje", record.get("hviga_laje_m")),
        ]

        def render(items):
            lines = []
            for item in items:
                label, value, *unit = item
                rendered = "Não informado" if value is None else str(value)
                if unit and value is not None:
                    rendered = f"{rendered} {unit[0]}"
                lines.append(f"{label}: {rendered}")
            return "\n".join(lines)

        self.bridge_tab_labels["identification"].setText(
            render(identity_fields) + "\n\nEstado cadastral: não validado."
        )
        self.bridge_tab_labels["geometry"].setText(
            render(geometry_fields) + "\n\nMedidas exibidas conforme os campos de origem."
        )
        self.bridge_tab_labels["quantities"].setText(
            render(fields[7:]) + "\n\nDefinições e fórmulas dos indicadores ainda dependem de aprovação da engenharia."
        )
        pending = "Módulo ainda não integrado ao cadastro OAE."
        self.bridge_tab_labels["inspections"].setText(pending)
        self.bridge_tab_labels["documents"].setText(
            "Vínculo documental específico da OAE ainda não integrado.\n" + pending
        )
        self.bridge_tab_labels["history"].setText(
            source + f"\n\nID interno do registro: {record.source_row}\n"
            "Histórico de alterações e trilha de auditoria ainda não integrados."
        )

    def _import_page(self) -> QWidget:
        """Import page matching the approved PDF: upload area, five vertical steps and integrity note."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("importPageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)

        heading = QLabel("Importar tabela de engenharia")
        heading.setMinimumHeight(32)
        heading.setStyleSheet("font-size:16pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Traga planilhas existentes para o PONTE mantendo a origem e a rastreabilidade."
        )
        subtitle.setObjectName("sectionIntro")
        subtitle.setMinimumHeight(25)
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        management_row = QHBoxLayout()
        management_row.addStretch(1)
        manage_tables = QPushButton("Gerenciar tabelas existentes")
        manage_tables.setObjectName("secondaryAction")
        manage_tables.setCheckable(True)
        manage_tables.toggled.connect(self._toggle_table_manager)
        management_row.addWidget(manage_tables)
        layout.addLayout(management_row)

        self.table_manager_panel = QFrame()
        self.table_manager_panel.setObjectName("tableManagerPanel")
        self.table_manager_panel.setStyleSheet(
            "QFrame#tableManagerPanel {background:#ffffff;border:1px solid #dce5ed;border-radius:8px;}"
        )
        manager_layout = QVBoxLayout(self.table_manager_panel)
        manager_layout.setContentsMargins(14, 12, 14, 12)
        manager_layout.setSpacing(9)
        manager_heading = QLabel("Gerenciamento de tabelas")
        manager_heading.setStyleSheet("font-size:12pt;font-weight:700;color:#26384b;border:0;")
        manager_layout.addWidget(manager_heading)
        manager_intro = QLabel(
            "Gerencie as tabelas deste projeto sem sair da tela de importação."
        )
        manager_intro.setObjectName("muted")
        manager_intro.setStyleSheet("border:0;")
        manager_layout.addWidget(manager_intro)
        manager_project_row = QHBoxLayout()
        manager_project_row.addWidget(QLabel("Projeto"))
        self.manager_project_combo = QComboBox()
        for project in self.store.list_projects():
            self.manager_project_combo.addItem(project["name"], project["id"])
        self.manager_project_combo.currentIndexChanged.connect(self._refresh_table_manager)
        manager_project_row.addWidget(self.manager_project_combo, 1)
        manager_layout.addLayout(manager_project_row)
        self.manager_tables_grid = QTableWidget(0, 3)
        self.manager_tables_grid.setHorizontalHeaderLabels(
            ["Nome da tabela", "Registros", "Última atualização"]
        )
        self.manager_tables_grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.manager_tables_grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.manager_tables_grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.manager_tables_grid.verticalHeader().setVisible(False)
        self.manager_tables_grid.horizontalHeader().setStretchLastSection(True)
        self.manager_tables_grid.setAlternatingRowColors(True)
        self.manager_tables_grid.setMinimumHeight(150)
        self.manager_tables_grid.setMaximumHeight(230)
        manager_layout.addWidget(self.manager_tables_grid)
        manager_actions = QHBoxLayout()
        rename_managed = QPushButton("Renomear selecionada")
        rename_managed.clicked.connect(self._rename_managed_table)
        delete_managed = QPushButton("Excluir selecionada")
        delete_managed.setStyleSheet(
            "QPushButton {color:#a12d2d;border:1px solid #d8a4a4;padding:7px 12px;}"
            "QPushButton:hover {background:#fff0f0;}"
        )
        delete_managed.clicked.connect(self._delete_managed_table)
        manager_actions.addWidget(rename_managed)
        manager_actions.addWidget(delete_managed)
        manager_actions.addStretch(1)
        manager_layout.addLayout(manager_actions)
        self.table_manager_panel.hide()
        layout.addWidget(self.table_manager_panel)

        # Large, uncluttered drop zone as shown in the approved import screen.
        drop_area = FileDropFrame(self.select_import_file)
        drop_area.setObjectName("importDropArea")
        drop_area.setMinimumHeight(154)
        drop_area.setStyleSheet(
            "QFrame#importDropArea {background:#ffffff;border:1px dashed #8fb4d0;"
            "border-radius:8px;}"
        )
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setContentsMargins(22, 17, 22, 17)
        drop_layout.setSpacing(8)

        drop_title = QLabel("Arraste um arquivo Excel ou CSV para esta área")
        drop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_title.setMinimumHeight(30)
        drop_title.setWordWrap(True)
        drop_title.setStyleSheet("font-size:12pt;font-weight:700;color:#294b67;border:0;")
        drop_detail = QLabel(
            ".xlsx  •  .xls  •  .csv  |  O arquivo original será preservado"
        )
        drop_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_detail.setMinimumHeight(24)
        drop_detail.setWordWrap(True)
        drop_detail.setObjectName("muted")
        drop_detail.setStyleSheet("border:0;")
        choose = QPushButton("Selecionar arquivo")
        choose.setObjectName("primaryAction")
        choose.setMinimumHeight(42)
        choose.setMinimumWidth(168)
        choose.clicked.connect(self.select_import_file)

        drop_layout.addWidget(drop_title)
        drop_layout.addWidget(drop_detail)
        drop_layout.addWidget(choose, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(drop_area)

        steps = Panel("Etapas de importação")
        steps.body.setSpacing(2)
        step_data = [
            ("01", "Selecionar arquivo",
             "Escolha o arquivo e as abas que deseja importar.", "Disponível"),
            ("02", "Conferir prévia",
             "Revise cabeçalhos, linhas, tipos e valores originais.", "Disponível"),
            ("03", "Mapear colunas",
             "Associe campos, unidades e escopo com confirmação.", "Em preparação"),
            ("04", "Validar dados",
             "Identifique ausências, duplicidades e inconsistências.", "Em preparação"),
            ("05", "Importar e analisar",
             "Grave os dados e abra a análise do conjunto importado.", "Importação disponível"),
        ]

        for index, (number, title, detail, status) in enumerate(step_data):
            row = QFrame()
            row.setObjectName("importStepRow")
            row.setStyleSheet(
                "QFrame#importStepRow {background:transparent;border:0;}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(2, 7, 2, 7)
            row_layout.setSpacing(14)

            number_label = QLabel(number)
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setFixedSize(34, 34)
            number_label.setStyleSheet(
                "background:#eaf3fa;color:#287db5;border-radius:17px;"
                "font-size:9pt;font-weight:700;border:0;"
            )

            text_column = QVBoxLayout()
            text_column.setContentsMargins(0, 0, 0, 0)
            text_column.setSpacing(3)
            title_label = QLabel(title)
            title_label.setMinimumHeight(23)
            title_label.setStyleSheet(
                "font-size:10pt;font-weight:700;color:#34485c;border:0;"
            )
            detail_label = QLabel(detail)
            detail_label.setMinimumHeight(21)
            detail_label.setWordWrap(True)
            detail_label.setObjectName("mutedSmall")
            detail_label.setStyleSheet("border:0;")
            text_column.addWidget(title_label)
            text_column.addWidget(detail_label)

            status_label = QLabel(status)
            status_label.setMinimumHeight(22)
            status_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            status_label.setObjectName("mutedSmall")
            status_label.setStyleSheet("border:0;")

            row_layout.addWidget(number_label, 0, Qt.AlignmentFlag.AlignVCenter)
            row_layout.addLayout(text_column, 1)
            row_layout.addWidget(status_label, 0, Qt.AlignmentFlag.AlignVCenter)
            steps.body.addWidget(row)

            if index < len(step_data) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFixedHeight(1)
                separator.setStyleSheet("background:#edf1f5;border:0;")
                steps.body.addWidget(separator)

        layout.addWidget(steps)

        integrity = QLabel(
            "Princípio de integridade: nenhuma unidade, fórmula ou valor será corrigido silenciosamente."
        )
        integrity.setMinimumHeight(42)
        integrity.setWordWrap(True)
        integrity.setStyleSheet(
            "background:#fff5e5;color:#93621f;padding:11px 14px;border-radius:6px;"
        )
        layout.addWidget(integrity)
        layout.addStretch(1)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        return page

    def select_import_file(self, selected_path=None):
        """Preview a source file and resolve table-name conflicts before importing."""
        path = selected_path
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar planilha de engenharia",
                "",
                "Planilhas e dados (*.xlsx *.xlsm *.xls *.xlsb *.csv);;Todos os arquivos (*.*)",
            )
        if not path:
            return

        projects = self.store.list_projects()
        if not projects:
            name, accepted = QInputDialog.getText(
                self, "Projeto de destino", "Não há projetos cadastrados. Nome do novo projeto:"
            )
            if not accepted or not name.strip():
                return
            try:
                project_id = self.store.create_project(name.strip())
            except Exception as exc:
                QMessageBox.warning(self, "Projeto", str(exc))
                return
        else:
            labels = [f"{item['name']}  ·  ID {item['id']}" for item in projects]
            selected, accepted = QInputDialog.getItem(
                self, "Projeto de destino", "Importar para:", labels, 0, False
            )
            if not accepted:
                return
            project_id = projects[labels.index(selected)]["id"]

        exchange = SpreadsheetExchange(self.store)
        suffix = Path(path).suffix.casefold()
        try:
            if suffix == ".csv":
                preview = exchange.preview_csv(path, limit=5)
                rows = preview.get("rows", [])
                preview_text = "\n".join("  |  ".join(map(str, row[:6])) for row in rows[:6])
                source_names = [Path(path).stem]
            elif suffix in {".xls", ".xlsb"}:
                preview = (
                    exchange.preview_xls(path, limit=5)
                    if suffix == ".xls"
                    else exchange.preview_xlsb(path, limit=5)
                )
                preview_text = self._format_sheet_preview(preview.get("sheets", []))
                source_names = [item["sheet_name"] for item in preview.get("sheets", [])]
            elif suffix in {".xlsx", ".xlsm"}:
                preview = exchange.preview_xlsx(path, limit=5)
                preview_text = self._format_sheet_preview(preview.get("sheets", []))
                source_names = [item["sheet_name"] for item in preview.get("sheets", [])]
            else:
                QMessageBox.warning(self, "Formato não suportado", "Selecione XLSX, XLSM, XLS, XLSB ou CSV.")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Não foi possível ler a planilha", str(exc))
            return

        existing_tables = self.store.list_tables(project_id)
        existing_by_name = {item["name"].casefold(): item for item in existing_tables}
        conflicts = [name for name in source_names if name.casefold() in existing_by_name]
        strategy = "normal"
        table_names = {}
        staged_names = {}
        if conflicts:
            conflict_text = "\n".join(f"• {name}" for name in conflicts)
            choice = QMessageBox(self)
            choice.setWindowTitle("Tabelas com nomes existentes")
            choice.setIcon(QMessageBox.Icon.Warning)
            choice.setText(
                "O projeto já contém tabela(s) com estes nomes:\n\n"
                f"{conflict_text}\n\n"
                "Escolha como deseja continuar. A substituição só acontece depois "
                "que a nova planilha for importada com sucesso."
            )
            replace_button = choice.addButton(
                "Substituir existentes", QMessageBox.ButtonRole.DestructiveRole
            )
            rename_button = choice.addButton(
                "Importar com outro nome", QMessageBox.ButtonRole.AcceptRole
            )
            choice.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            choice.exec()
            clicked = choice.clickedButton()
            if clicked is replace_button:
                strategy = "replace"
            elif clicked is rename_button:
                strategy = "rename"
            else:
                return

            used_names = {item["name"].casefold() for item in existing_tables}
            for index, name in enumerate(conflicts, start=1):
                if strategy == "replace":
                    candidate = f"__PONTE_STAGING_{project_id}_{index}__"
                    while candidate.casefold() in used_names:
                        candidate += "_"
                    table_names[name] = candidate
                    staged_names[name] = candidate
                    used_names.add(candidate.casefold())
                else:
                    candidate = f"{name} (2)"
                    number = 2
                    while candidate.casefold() in used_names:
                        number += 1
                        candidate = f"{name} ({number})"
                    table_names[name] = candidate
                    used_names.add(candidate.casefold())

        question = QMessageBox(self)
        question.setWindowTitle("Conferir prévia da importação")
        question.setIcon(QMessageBox.Icon.Information)
        question.setText(
            f"Arquivo: {Path(path).name}\n\nPrévia das primeiras linhas:\n{preview_text[:5000]}\n\n"
            "A importação criará uma tabela por aba (Excel) ou uma tabela (CSV). "
            "Os valores originais não serão corrigidos automaticamente. Continuar?"
        )
        question.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        question.setDefaultButton(QMessageBox.StandardButton.No)
        if question.exec() != QMessageBox.StandardButton.Yes:
            return

        created = []
        try:
            if suffix == ".csv":
                target_name = table_names.get(source_names[0], source_names[0])
                created = [exchange.import_csv(project_id, path, table_name=target_name)]
            elif suffix == ".xls":
                created = exchange.import_xls(project_id, path, table_names=table_names)
            elif suffix == ".xlsb":
                created = exchange.import_xlsb(project_id, path, table_names=table_names)
            else:
                created = exchange.import_xlsx(project_id, path, table_names=table_names)

            if strategy == "replace":
                current_tables = self.store.list_tables(project_id)
                current_by_name = {item["name"]: item for item in current_tables}
                replacements = []
                for original_name, staged_name in staged_names.items():
                    old = existing_by_name[original_name.casefold()]
                    staged = current_by_name.get(staged_name)
                    if staged is not None:
                        replacements.append((old["id"], staged["id"], original_name))
                if replacements:
                    self.store.replace_tables(replacements)
        except Exception as exc:
            if strategy == "replace":
                for table_id in created:
                    try:
                        self.store.delete_table(table_id)
                    except Exception:
                        pass
            QMessageBox.critical(self, "Falha na importação", str(exc))
            return

        self.refresh_pages()
        self.navigate("Importar dados")
        QMessageBox.information(
            self,
            "Importação concluída",
            f"{len(created)} tabela(s) criada(s) no projeto selecionado.\n"
            "Os dados foram gravados no workspace local.\n"
            "O arquivo de origem permaneceu no local original.",
        )

    @staticmethod
    def _format_sheet_preview(sheets):
        lines = []
        for sheet in sheets[:5]:
            lines.append(f"Aba: {sheet.get('sheet_name', '—')}")
            for row in sheet.get("rows", [])[:5]:
                lines.append("  |  ".join(map(str, row[:6])))
        return "\n".join(lines) or "Nenhuma linha encontrada na prévia."

    def _analysis_page(self) -> QWidget:
        """Engineering analysis layout; unavailable calculations are never fabricated."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        intro = QVBoxLayout()
        heading = QLabel("Análise de dados de pontes e OAEs")
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Defina intervalos, combine critérios e examine apenas amostras tecnicamente comparáveis."
        )
        subtitle.setObjectName("sectionIntro")
        intro.addWidget(heading)
        intro.addWidget(subtitle)
        layout.addLayout(intro)

        scope = Panel("CONJUNTO DE DADOS", "Escopo da análise")
        scope_row = QHBoxLayout()
        dataset = QComboBox()
        dataset.addItem("Conjuntos importados — integração pendente")
        dataset.setEnabled(False)
        entity_scope = QComboBox()
        entity_scope.addItem("Todas as OAEs — cadastro não integrado")
        entity_scope.setEnabled(False)
        scope_row.addWidget(QLabel("Conjunto"))
        scope_row.addWidget(dataset, 2)
        scope_row.addWidget(QLabel("Escopo"))
        scope_row.addWidget(entity_scope, 2)
        scope.body.addLayout(scope_row)
        layout.addWidget(scope)

        content = QHBoxLayout()
        filters = Panel("Filtros por intervalo", "Campos previstos no design de análise")
        filter_grid = QGridLayout()
        filter_grid.addWidget(QLabel("Grandeza"), 0, 0)
        filter_grid.addWidget(QLabel("Mínimo"), 0, 1)
        filter_grid.addWidget(QLabel("Máximo"), 0, 2)
        for row, label in enumerate(
            ("Comprimento total (m)", "Largura do tabuleiro (m)",
             "Área do tabuleiro (m²)", "Volume de concreto (m³)"), start=1
        ):
            filter_grid.addWidget(QLabel(label), row, 0)
            minimum = QLineEdit()
            maximum = QLineEdit()
            minimum.setPlaceholderText("Mín.")
            maximum.setPlaceholderText("Máx.")
            minimum.setEnabled(False)
            maximum.setEnabled(False)
            filter_grid.addWidget(minimum, row, 1)
            filter_grid.addWidget(maximum, row, 2)
        filters.body.addLayout(filter_grid)
        filter_note = QLabel(
            "Filtros serão habilitados quando o repositório de OAEs e os campos geométricos "
            "estiverem conectados."
        )
        filter_note.setObjectName("mutedSmall")
        filter_note.setWordWrap(True)
        filters.body.addWidget(filter_note)
        content.addWidget(filters, 1)

        results = Panel("Resultados da seleção", "Indicadores de engenharia — sem valores presumidos")
        metrics = QGridLayout()
        metric_names = [
            ("Paf", "kg/m²"), ("Pap", "kg/m²"), ("Ecm", "m³/m²"),
            ("Af", "m²/m²"), ("Aço total indicativo", "kg/m²"),
            ("Aço total indicativo", "kg/m³"),
        ]
        for index, (name, unit) in enumerate(metric_names):
            card = QFrame()
            card.setStyleSheet(
                "QFrame {background:#eaf3fa;border:1px solid #d7e6f1;border-radius:6px;}"
            )
            box = QVBoxLayout(card)
            box.setContentsMargins(10, 9, 10, 9)
            label = QLabel(name)
            label.setObjectName("mutedSmall")
            value = QLabel("Não calculado")
            value.setStyleSheet("font-size:14pt;font-weight:700;color:#294b67;")
            unit_label = QLabel(unit + " • fórmula/validação pendente")
            unit_label.setObjectName("mutedSmall")
            unit_label.setWordWrap(True)
            box.addWidget(label)
            box.addWidget(value)
            box.addWidget(unit_label)
            metrics.addWidget(card, index // 3, index % 3)
        results.body.addLayout(metrics)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["Identificação", "Tipologia", "Vão total (m)", "Concreto (m³)", "Aço (kg)", "Status"]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumHeight(170)
        results.body.addWidget(table, 1)
        empty = QLabel(
            "Nenhuma amostra exibida. O cadastro técnico e os critérios de comparabilidade "
            "ainda não estão conectados."
        )
        empty.setObjectName("mutedSmall")
        empty.setWordWrap(True)
        results.body.addWidget(empty)
        content.addWidget(results, 2)
        layout.addLayout(content, 1)

        note = QLabel(
            "Nota metodológica: Paf, Pap, Ecm, Af e os indicadores de aço dependem de "
            "definições, unidades e fórmulas aprovadas pela EGT. Nenhum resultado é estimado nesta tela."
        )
        note.setWordWrap(True)
        note.setStyleSheet("background:#fff5e5;color:#93621f;padding:11px;border-radius:6px;")
        layout.addWidget(note)
        return page

    def _reports_page(self) -> QWidget:
        """Report catalog layout; generation stays disabled until validated data exists."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        heading = QLabel("Transforme análises em entregáveis rastreáveis")
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Gere relatórios a partir de conjuntos filtrados, preservando metodologia, versão e evidências."
        )
        subtitle.setObjectName("sectionIntro")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        models = Panel(
            "Modelos de relatório",
            "A geração será habilitada quando os dados e as fórmulas estiverem validados."
        )
        row = QHBoxLayout()
        for title, detail in [
            ("Resumo executivo", "Indicadores gerais, escopo e pendências."),
            ("Comparativo de OAEs", "Amostras compatíveis e critérios aplicados."),
            ("Relatório de importação", "Origem, mapeamento e validações."),
            ("Mapa de quantitativos", "Valores por OAE e status de validação."),
        ]:
            card = QFrame()
            card.setStyleSheet(
                "QFrame {background:#eaf3fa;border:1px solid #d7e6f1;border-radius:7px;}"
            )
            box = QVBoxLayout(card)
            box.setContentsMargins(12, 12, 12, 12)
            name = QLabel(title)
            name.setStyleSheet("font-weight:700;color:#294b67;")
            desc = QLabel(detail)
            desc.setObjectName("mutedSmall")
            desc.setWordWrap(True)
            action = QPushButton("Aguardando integração")
            action.setEnabled(False)
            box.addWidget(name)
            box.addWidget(desc)
            box.addStretch()
            box.addWidget(action)
            row.addWidget(card, 1)
        models.body.addLayout(row)
        layout.addWidget(models)

        history = Panel(
            "Histórico de relatórios",
            "Filtros, escopo, versão do cálculo e data de geração"
        )
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["Relatório", "Escopo", "Formato", "Gerado em", "Versão", "Status"]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        history.body.addWidget(table, 1)
        empty = QLabel("Nenhum relatório foi gerado neste workspace.")
        empty.setObjectName("mutedSmall")
        history.body.addWidget(empty)
        layout.addWidget(history, 1)

        note = QLabel(
            "Todo relatório deverá exibir filtros, tamanho e critérios da amostra, exclusões, "
            "unidades, origem, fórmulas e versão metodológica. Estimativas não serão apresentadas "
            "como quantitativos executivos."
        )
        note.setWordWrap(True)
        note.setStyleSheet("background:#fff5e5;color:#93621f;padding:11px;border-radius:6px;")
        layout.addWidget(note)
        return page

    def _documents_page(self) -> QWidget:
        """Local document catalog with search, status filtering and source inspection."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        heading = QLabel("Repositório documental do empreendimento")
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Consulte arquivos indexados neste dispositivo. O catálogo preserva o caminho, "
            "o hash e o resultado da extração; indexação não significa aprovação técnica."
        )
        subtitle.setObjectName("sectionIntro")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.document_rows = self.documents.list_documents()
        self.document_metrics = self._metric_row([
            MetricCard("Documentos indexados", str(len(self.document_rows)), "Catálogo local"),
            MetricCard("Extração concluída", str(sum(d.get("status") == "success" for d in self.document_rows)), "Leitura sem avisos"),
            MetricCard("Aguardando revisão", str(sum(d.get("status") in ("partial", "error", "unsupported") for d in self.document_rows)), "Exige conferência"),
            MetricCard("Versões", "Não apurado", "Versionamento documental ainda não integrado"),
        ])
        layout.addWidget(self.document_metrics)

        panel = Panel("Biblioteca de documentos", "Metadados disponíveis • versões e vínculo com OAEs ainda não integrados")
        toolbar = QHBoxLayout()
        self.document_search = QLineEdit()
        self.document_search.setPlaceholderText("Buscar nome, extensão ou caminho…")
        self.document_search.textChanged.connect(self._filter_documents)
        toolbar.addWidget(self.document_search, 2)
        self.document_status_filter = QComboBox()
        self.document_status_filter.addItem("Todas as situações", "")
        self.document_type_filter = QComboBox()
        self.document_type_filter.addItem("Todos os formatos", "")
        for value in sorted({str(d.get("status") or "") for d in self.document_rows if d.get("status")}):
            self.document_status_filter.addItem(value, value)
        for value in sorted({str(d.get("extension") or "") for d in self.document_rows if d.get("extension")}):
            self.document_type_filter.addItem(value, value)
        self.document_status_filter.currentIndexChanged.connect(self._filter_documents)
        self.document_type_filter.currentIndexChanged.connect(self._filter_documents)
        toolbar.addWidget(self.document_status_filter)
        toolbar.addWidget(self.document_type_filter)
        add = QPushButton("+ Adicionar documento")
        add.setObjectName("primaryAction")
        add.clicked.connect(self.add_documents)
        toolbar.addWidget(add)
        panel.body.addLayout(toolbar)

        self.document_table = QTableWidget(len(self.document_rows), 5)
        self.document_table.setHorizontalHeaderLabels([
            "Documento", "Categoria", "Vinculado a", "Tamanho", "Situação"
        ])
        self.document_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.document_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.document_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.document_table.verticalHeader().setVisible(False)
        self.document_table.horizontalHeader().setStretchLastSection(True)
        for row, doc in enumerate(self.document_rows):
            metadata = {}
            values = [
                doc.get("file_name"),
                doc.get("extension"),
                "Não vinculado",
                f"{doc.get('size_bytes', 0):,} bytes".replace(",", "."),
                doc.get("status"),
            ]
            for col, value in enumerate(values):
                self.document_table.setItem(
                    row, col, QTableWidgetItem("Não informado" if value is None else str(value))
                )
        self.document_table.itemSelectionChanged.connect(self._show_selected_document)
        panel.body.addWidget(self.document_table, 1)
        layout.addWidget(panel, 2)

        detail = Panel("Detalhes e rastreabilidade", "Selecione um documento para consultar a origem e os metadados")
        self.document_detail = QLabel(
            "Nenhum documento selecionado. Use “Adicionar documento” para indexar arquivos locais."
        )
        self.document_detail.setObjectName("sectionIntro")
        self.document_detail.setWordWrap(True)
        detail.body.addWidget(self.document_detail)
        actions = QHBoxLayout()
        self.open_document_button = QPushButton("Abrir arquivo original")
        self.open_document_button.setObjectName("secondaryAction")
        self.open_document_button.setEnabled(False)
        self.open_document_button.clicked.connect(self.open_selected_document)
        actions.addWidget(self.open_document_button)
        actions.addStretch()
        detail.body.addLayout(actions)
        layout.addWidget(detail, 1)

        if self.document_rows:
            self.document_table.selectRow(0)
        return page

    def _filter_documents(self, *_):
        if not hasattr(self, "document_table"):
            return
        needle = self.document_search.text().strip().casefold()
        status = self.document_status_filter.currentData()
        extension = self.document_type_filter.currentData()
        for row, doc in enumerate(self.document_rows):
            matches_text = not needle or needle in " ".join(
                str(doc.get(key) or "") for key in ("file_name", "extension", "path")
            ).casefold()
            matches_status = not status or doc.get("status") == status
            matches_extension = not extension or doc.get("extension") == extension
            self.document_table.setRowHidden(
                row, not (matches_text and matches_status and matches_extension)
            )

    def add_documents(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Adicionar documentos ao catálogo", "",
            "Documentos suportados (*.pdf *.doc *.docx *.ppt *.pptx *.rtf *.odt *.odp "
            "*.xlsx *.xlsm *.xls *.xlsb *.csv *.txt *.md *.json *.xml *.dxf *.dwg "
            "*.ifc *.rvt *.rfa *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.gif);;"
            "Todos os arquivos (*.*)"
        )
        if not paths:
            return
        try:
            scanner = DocumentScanner()
            results = scanner.scan_many(paths)
            for result in results:
                self.documents.index_result(result)
            self.refresh_document_page()
            failures = sum(result.status in ("error", "partial", "unsupported") for result in results)
            QMessageBox.information(
                self, "Indexação concluída",
                f"{len(results)} arquivo(s) processado(s).\n"
                f"{failures} arquivo(s) com avisos, falhas ou formato sem leitor. "
                "A extração não representa validação técnica."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Falha ao indexar documentos", str(exc))

    def refresh_document_page(self):
        current = self.stack.currentIndex()
        self.stack.removeWidget(self.pages["Documentos"])
        self.pages["Documentos"].deleteLater()
        new_page = self._documents_page()
        self.pages["Documentos"] = new_page
        self.stack.insertWidget(5, new_page)
        self.stack.setCurrentIndex(current)

    def _selected_document(self):
        if not hasattr(self, "document_table"):
            return None
        selected = self.document_table.selectionModel().selectedRows()
        if not selected:
            return None
        return self.document_rows[selected[0].row()]

    def _show_selected_document(self):
        doc = self._selected_document()
        if not doc:
            self.document_detail.setText("Nenhum documento selecionado.")
            self.open_document_button.setEnabled(False)
            return
        full = self.documents.get_document(doc["id"])
        metadata = full.get("metadata", {})
        warnings = full.get("warnings", [])
        errors = full.get("errors", [])
        details = [
            f"Nome original: {full.get('file_name')}",
            f"Caminho: {full.get('path')}",
            f"SHA-256: {full.get('sha256')}",
            f"Tamanho: {full.get('size_bytes')} bytes",
            f"Formato: {full.get('extension')}",
            f"Situação da extração: {full.get('status')}",
            f"Seções extraídas: {len(full.get('sections', []))}",
            f"Data da indexação: {full.get('scanned_at')}",
            "Vínculo com projeto/OAE: não integrado",
            "Versionamento e permissões: não integrados",
        ]
        if metadata:
            details.append("Metadados: " + str(metadata))
        if warnings:
            details.append("Avisos: " + " | ".join(map(str, warnings)))
        if errors:
            details.append("Erros: " + " | ".join(map(str, errors)))
        self.document_detail.setText("\n".join(details))
        self.open_document_button.setEnabled(Path(full.get("path", "")).is_file())

    def open_selected_document(self):
        doc = self._selected_document()
        if not doc:
            return
        full = self.documents.get_document(doc["id"])
        path = Path(full.get("path", ""))
        if not path.is_file():
            QMessageBox.warning(self, "Arquivo não encontrado", "O arquivo original não está mais nesse caminho.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _module_page(self, title: str, description: str, action: str, callback) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = Panel(title, description)
        note = QLabel("Estado da integração: módulo em construção. Esta tela não usa números fictícios nem declara cálculos como validados.")
        note.setWordWrap(True)
        note.setStyleSheet("background:#f4f7fa;color:#607286;padding:14px;border-radius:6px;")
        panel.body.addWidget(note)
        button = QPushButton(action)
        button.setObjectName("primaryAction")
        button.clicked.connect(callback)
        panel.body.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _toggle_table_manager(self, visible: bool):
        self.table_manager_panel.setVisible(visible)
        if visible:
            self._refresh_table_manager()

    def _refresh_table_manager(self, *args):
        grid = getattr(self, "manager_tables_grid", None)
        project_combo = getattr(self, "manager_project_combo", None)
        if grid is None or project_combo is None:
            return
        grid.setRowCount(0)
        project_id = project_combo.currentData()
        if project_id is None:
            return
        for item in self.store.list_tables(project_id):
            row = grid.rowCount()
            grid.insertRow(row)
            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            grid.setItem(row, 0, name_item)
            grid.setItem(row, 1, QTableWidgetItem(
                str(len(self.store.list_records(item["id"])))
            ))
            grid.setItem(row, 2, QTableWidgetItem(
                str(item.get("updated_at") or "—")
            ))
        grid.resizeColumnsToContents()

    def _selected_managed_table(self):
        grid = getattr(self, "manager_tables_grid", None)
        if grid is None:
            return None, None
        row = grid.currentRow()
        item = grid.item(row, 0) if row >= 0 else None
        if item is None:
            return None, None
        return item.data(Qt.ItemDataRole.UserRole), item.text()

    def _rename_managed_table(self):
        table_id, current_name = self._selected_managed_table()
        if table_id is None:
            QMessageBox.information(self, "Renomear tabela", "Selecione uma tabela.")
            return
        new_name, accepted = QInputDialog.getText(
            self, "Renomear tabela", "Novo nome:", text=current_name
        )
        if not accepted or not new_name.strip() or new_name.strip() == current_name:
            return
        try:
            self.store.update_table(table_id, name=new_name.strip())
        except Exception as exc:
            QMessageBox.warning(self, "Não foi possível renomear", str(exc))
            return
        self._refresh_table_manager()
        self.refresh_pages()

    def _delete_managed_table(self):
        table_id, current_name = self._selected_managed_table()
        if table_id is None:
            QMessageBox.information(self, "Excluir tabela", "Selecione uma tabela.")
            return
        count = len(self.store.list_records(table_id))
        answer = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir a tabela '{current_name}' e seus {count} registro(s)?\\n\\n"
            "Esta ação também remove as colunas e não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.store.delete_table(table_id)
        self._refresh_table_manager()
        self.refresh_pages()

    def refresh_pages(self):
        current = self.stack.currentIndex()
        self.stack.removeWidget(self.pages["Projetos e obras"])
        self.pages["Projetos e obras"].deleteLater()
        new_page = self._projects_page()
        self.pages["Projetos e obras"] = new_page
        self.stack.insertWidget(1, new_page)
        self.stack.setCurrentIndex(current)
