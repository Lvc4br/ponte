"""PONTE v2 application shell aligned with the approved desktop design system.

The shell provides persistent module navigation and a light operational workspace.
Only values backed by local stores are shown as metrics; unavailable indicators are
explicitly marked as not yet calculated.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QMainWindow, QMessageBox, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QComboBox, QLineEdit, QFileDialog, QTabWidget,
)

from app.documents.index import DocumentIndex
from app.ui.engineering_workspace import EngineeringWorkspaceWindow
from app.workspace.store import WorkspaceStore
from app.workspace.exchange import SpreadsheetExchange
from app.data.dataset_store import DEFAULT_STORE, DatasetStore


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
        self.legacy_window = None
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
        org = QLabel("EGT Engenharia   •   Workspace local")
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
            "Importar dados": "Importar dados",
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
        intro = QLabel("Visão consolidada dos empreendimentos. Cadastre projetos e acompanhe sua estrutura local.")
        intro.setObjectName("sectionIntro")
        layout.addWidget(intro)
        projects = self.store.list_projects()
        cards = self._metric_row([
            MetricCard("Projetos cadastrados", str(len(projects)), "Registros no workspace"),
            MetricCard("OAEs vinculadas", "Não apurado", "Vínculo projeto–OAE ainda não integrado"),
            MetricCard("Em execução", "Não apurado", "Etapas ainda não estruturadas"),
            MetricCard("Com pendências", "Não apurado", "Validação ainda não integrada"),
        ])
        layout.addWidget(cards)
        panel = Panel("Empreendimentos cadastrados", "Dados efetivamente gravados no workspace local")
        create = QPushButton("+ Novo projeto")
        create.setObjectName("primaryAction")
        create.clicked.connect(self.create_project)
        panel.body.addWidget(create, 0, Qt.AlignmentFlag.AlignRight)
        table = QTableWidget(len(projects), 3)
        table.setHorizontalHeaderLabels(["Projeto / contrato", "Descrição", "Atualizado em"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        for row, project in enumerate(projects):
            for col, key in enumerate(("name", "description", "updated_at")):
                table.setItem(row, col, QTableWidgetItem(str(project.get(key) or "—")))
        panel.body.addWidget(table, 1)
        layout.addWidget(panel, 1)
        return page

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
        minimum = values.get("vao_min_m", values.get("vão_min_m"))
        maximum = values.get("vao_max_m", values.get("vão_max_m"))
        if minimum is None and maximum is None:
            return "Não informado"
        if minimum is None:
            return str(maximum)
        if maximum is None or maximum == minimum:
            return str(minimum)
        return f"{minimum} – {maximum}"

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
        """Import workflow screen from the approved PONTE design, not the spreadsheet grid."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        intro = QVBoxLayout()
        heading = QLabel("Importar tabela de engenharia")
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Traga planilhas existentes para o PONTE mantendo o arquivo original, "
            "a origem dos dados e a rastreabilidade."
        )
        subtitle.setObjectName("sectionIntro")
        subtitle.setWordWrap(True)
        intro.addWidget(heading)
        intro.addWidget(subtitle)
        layout.addLayout(intro)

        upload = Panel("Selecionar arquivo", "Entrada de planilhas para validação")
        drop_area = FileDropFrame(self.select_import_file)
        drop_area.setStyleSheet(
            "QFrame {background:#eaf3fa;border:1px dashed #8fb4d0;border-radius:8px;}"
        )
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setContentsMargins(24, 28, 24, 28)
        drop_layout.setSpacing(10)
        drop_title = QLabel("Selecione uma planilha Excel ou CSV para pré-visualizar")
        drop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_title.setStyleSheet("font-size:12pt;font-weight:700;color:#294b67;")
        drop_detail = QLabel(
            ".xlsx  •  .xls  •  .csv     |     O arquivo original será preservado"
        )
        drop_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_detail.setObjectName("muted")
        choose = QPushButton("Selecionar arquivo")
        choose.setObjectName("primaryAction")
        choose.clicked.connect(self.select_import_file)
        drop_layout.addWidget(drop_title)
        drop_layout.addWidget(drop_detail)
        drop_layout.addWidget(choose, 0, Qt.AlignmentFlag.AlignHCenter)
        upload.body.addWidget(drop_area)
        layout.addWidget(upload)

        steps = Panel("Etapas de importação")
        step_data = [
            ("01", "Selecionar arquivo", "Escolha o arquivo e as abas que deseja importar."),
            ("02", "Conferir prévia", "Revise as primeiras linhas, cabeçalhos e valores originais."),
            ("03", "Mapear colunas e unidades", "Etapa de mapeamento técnico ainda em preparação; os cabeçalhos originais são preservados."),
            ("04", "Validar dados", "A validação de unidades, duplicidades e comparabilidade de engenharia ainda não está integrada."),
            ("05", "Importar e analisar", "A importação genérica está disponível; a análise técnica depende das etapas anteriores."),
        ]
        for number, title, detail in step_data:
            line = QHBoxLayout()
            number_label = QLabel(number)
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setFixedSize(38, 38)
            number_label.setStyleSheet(
                "background:#eaf3fa;color:#287db5;border-radius:19px;font-weight:700;"
            )
            texts = QVBoxLayout()
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight:700;color:#34485c;")
            detail_label = QLabel(detail)
            detail_label.setObjectName("mutedSmall")
            texts.addWidget(title_label)
            texts.addWidget(detail_label)
            line.addWidget(number_label)
            line.addLayout(texts, 1)
            steps.body.addLayout(line)
        layout.addWidget(steps, 1)

        integrity = QLabel(
            "Princípio de integridade: nenhuma unidade, fórmula ou valor será corrigido silenciosamente."
        )
        integrity.setWordWrap(True)
        integrity.setStyleSheet(
            "background:#fff5e5;color:#93621f;padding:12px;border-radius:6px;"
        )
        layout.addWidget(integrity)
        return page

    def select_import_file(self, selected_path=None):
        """Preview a source file and import it into a selected local project after confirmation."""
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
            elif suffix in {".xls", ".xlsb"}:
                preview = (
                    exchange.preview_xls(path, limit=5)
                    if suffix == ".xls"
                    else exchange.preview_xlsb(path, limit=5)
                )
                preview_text = self._format_sheet_preview(preview.get("sheets", []))
            elif suffix in {".xlsx", ".xlsm"}:
                preview = exchange.preview_xlsx(path, limit=5)
                preview_text = self._format_sheet_preview(preview.get("sheets", []))
            else:
                QMessageBox.warning(self, "Formato não suportado", "Selecione XLSX, XLSM, XLS, XLSB ou CSV.")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Não foi possível ler a planilha", str(exc))
            return

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

        try:
            if suffix == ".csv":
                created = [exchange.import_csv(project_id, path)]
            elif suffix == ".xls":
                created = exchange.import_xls(project_id, path)
            elif suffix == ".xlsb":
                created = exchange.import_xlsb(project_id, path)
            else:
                created = exchange.import_xlsx(project_id, path)
            self.refresh_pages()
            QMessageBox.information(
                self,
                "Importação concluída",
                f"{len(created)} tabela(s) criada(s) no projeto selecionado.\n"
                "O arquivo de origem permaneceu no local original.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Falha na importação", str(exc))

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
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = Panel("Documentos indexados", "Arquivos analisados e catalogados neste dispositivo")
        docs = self.documents.list_documents()
        panel.body.addWidget(self._metric_row([
            MetricCard("Documentos indexados", str(len(docs)), "Catálogo local"),
            MetricCard("Aguardando revisão", str(sum(1 for d in docs if d.get("status") not in ("ok", "completed", "success"))), "Conforme status registrado"),
            MetricCard("Versões recentes", "Não apurado", "Versionamento documental ainda não integrado"),
        ]))
        table = QTableWidget(len(docs), 5)
        table.setHorizontalHeaderLabels(["Documento", "Formato", "Situação", "Seções", "Digitalizado em"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        for row, doc in enumerate(docs):
            values = [doc.get("file_name"), doc.get("extension"), doc.get("status"),
                      doc.get("section_count"), doc.get("scanned_at")]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value if value is not None else "—")))
        panel.body.addWidget(table, 1)
        layout.addWidget(panel, 1)
        return page

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

    def open_spreadsheet_workspace(self):
        """Open the spreadsheet editor as an auxiliary tool, not as a PONTE module page."""
        if self.legacy_window is None:
            self.legacy_window = EngineeringWorkspaceWindow()
            self.legacy_window.setWindowTitle(
                "PONTE | Ferramenta auxiliar de planilhas"
            )
        self.legacy_window.show()
        self.legacy_window.raise_()
        self.legacy_window.activateWindow()

    def refresh_pages(self):
        current = self.stack.currentIndex()
        self.stack.removeWidget(self.pages["Projetos e obras"])
        self.pages["Projetos e obras"].deleteLater()
        new_page = self._projects_page()
        self.pages["Projetos e obras"] = new_page
        self.stack.insertWidget(1, new_page)
        self.stack.setCurrentIndex(current)
