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
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QWidget, QScrollArea, QComboBox, QLineEdit,
    QFileDialog, QTabWidget,
)

from app.documents.index import DocumentIndex
from app.documents.scanner import DocumentScanner
from app.workspace.store import WorkspaceStore
from app.workspace.exchange import SpreadsheetExchange
from app.data.dataset_store import DEFAULT_STORE, DatasetStore
from app.core.bridge_formatters import bridge_span_text
from app.core.models import BridgeRecord


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

    def _workspace_datasets(self):
        """Return every imported workspace table with its schema and records."""
        result = []
        for project in self.store.list_projects():
            for table in self.store.list_tables(project["id"]):
                result.append({
                    "project": project,
                    "table": table,
                    "columns": self.store.list_columns(table["id"]),
                    "records": self.store.list_records(table["id"]),
                })
        return result

    @staticmethod
    def _filled(value):
        return value is not None and str(value).strip() not in ("", "—", "-", "nan", "None")

    @staticmethod
    def _pick_value(values, *names):
        for name in names:
            if name in values and values[name] not in (None, ""):
                return values[name]
        folded = {str(key).strip().casefold(): value for key, value in values.items()}
        for name in names:
            value = folded.get(str(name).strip().casefold())
            if value not in (None, ""):
                return value
        return None

    def _dataset_quality(self, dataset):
        rows = [record["values"] for record in dataset["records"]]
        columns = {column["name"].casefold() for column in dataset["columns"]}
        type_aliases = ("tipo_obra", "tipologia", "tipologia_obra", "tipo")
        length_aliases = ("compr_obra_m", "comprimento_total_m", "comprimento_m")
        width_aliases = ("largura_m", "largura_tabuleiro_m", "largura")
        span_aliases = ("vão_m", "vao_m", "vão_total_m", "vao_total_m", "vao_max_m", "vão_max_m")
        geometry_aliases = length_aliases + width_aliases + span_aliases
        geometry_columns = [name for name in geometry_aliases if name.casefold() in columns]
        typology = sum(self._filled(self._pick_value(row, *type_aliases)) for row in rows)
        identifiers = {
            str(self._pick_value(row, "obra", "identificador", "codigo_oae", "código_oae", "id_oae", "oae")).strip()
            for row in rows
            if self._filled(self._pick_value(row, "obra", "identificador", "codigo_oae", "código_oae", "id_oae", "oae"))
        }
        geometry = sum(
            self._filled(self._pick_value(row, *length_aliases))
            and self._filled(self._pick_value(row, *width_aliases))
            for row in rows
        )
        missing_geometry = (
            sum(any(not self._filled(self._pick_value(row, name)) for name in geometry_columns) for row in rows)
            if geometry_columns else None
        )
        quantity_columns = [
            column["name"] for column in dataset["columns"]
            if any(token in column["name"].casefold() for token in (
                "paf", "pap", "ecm", "af_", "aco", "aço", "concreto", "m3_m2", "kg_m2"
            ))
        ]
        # Only flag repeated quantity tuples for the same identified structure.
        # Equal quantities on different OAEs are not automatically duplicates.
        duplicate_quantities = None
        if quantity_columns and identifiers:
            seen = set()
            duplicate_quantities = 0
            for row in rows:
                identifier = self._pick_value(
                    row, "obra", "identificador", "codigo_oae", "código_oae", "id_oae", "oae"
                )
                quantities = tuple(
                    str(self._pick_value(row, name)) for name in quantity_columns
                )
                if not self._filled(identifier) or not any(
                    self._filled(self._pick_value(row, name)) for name in quantity_columns
                ):
                    continue
                key = (str(identifier).strip(), quantities)
                if key in seen:
                    duplicate_quantities += 1
                else:
                    seen.add(key)
        # Generic workspace records currently have no per-row source-file metadata.
        missing_origin = sum(
            not self._filled(self._pick_value(row, "origem", "source_file", "arquivo_origem", "fonte", "arquivo"))
            for row in rows
        )
        pending_records = 0
        for row in rows:
            lacks_type = not self._filled(self._pick_value(row, *type_aliases))
            lacks_geometry = (
                any(not self._filled(self._pick_value(row, name)) for name in geometry_columns)
                if geometry_columns else False
            )
            if lacks_type or lacks_geometry:
                pending_records += 1
        return {
            "records": len(rows), "typology": typology, "identifiers": len(identifiers),
            "geometry": geometry, "missing_geometry": missing_geometry,
            "duplicate_quantities": duplicate_quantities, "missing_origin": missing_origin,
            "pending_records": pending_records,
        }

    def _overview_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
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
        datasets = self._workspace_datasets()
        total_records = sum(len(item["records"]) for item in datasets)
        total_identified = sum(self._dataset_quality(item)["identifiers"] for item in datasets)
        candidates = sum(
            bool(item["records"]) and any(
                column.get("data_type") in ("integer", "decimal")
                for column in item["columns"]
            ) for item in datasets
        )
        qualities = [self._dataset_quality(item) for item in datasets]
        pending = sum(item["pending_records"] for item in qualities)
        layout.addWidget(self._metric_row([
            MetricCard("Projetos cadastrados", str(len(projects)), "Projetos no workspace local"),
            MetricCard("Registros de origem", str(total_records), "Linhas importadas; não equivalem automaticamente a OAEs"),
            MetricCard("Dados pendentes", str(pending), "Registros com tipologia ou geometria ausente", "#c58b3e"),
            MetricCard("Conjuntos candidatos", str(candidates), "Tabelas com dados numéricos; comparabilidade ainda não validada", "#4d9b8a"),
        ]))

        middle = QHBoxLayout()
        activity = Panel("Atividade recente", "Datas dos registros locais • não representa um log de auditoria")
        events = []
        for dataset in datasets:
            for record in dataset["records"]:
                stamp = record.get("updated_at") or record.get("created_at") or ""
                events.append((str(stamp), dataset["project"]["name"], dataset["table"]["name"], record["id"]))
        events.sort(key=lambda item: item[0], reverse=True)
        if events:
            for stamp, project_name, table_name, record_id in events[:5]:
                line = QHBoxLayout()
                label = QLabel(f"Registro #{record_id} • {table_name} / {project_name}")
                label.setStyleSheet("color:#46586b;")
                date_label = QLabel(stamp or "Data indisponível")
                date_label.setObjectName("mutedSmall")
                line.addWidget(label, 1)
                line.addWidget(date_label)
                activity.body.addLayout(line)
        else:
            empty = QLabel("Nenhum registro importado neste workspace.")
            empty.setObjectName("muted")
            activity.body.addWidget(empty)
        middle.addWidget(activity, 3)

        pending_panel = Panel("Pendências de validação", "Contagens derivadas dos campos presentes na tabela")
        duplicate_count = (
            sum(item["duplicate_quantities"] or 0 for item in qualities)
            if any(item["duplicate_quantities"] is not None for item in qualities) else None
        )
        geometry_count = (
            sum(item["missing_geometry"] or 0 for item in qualities)
            if any(item["missing_geometry"] is not None for item in qualities) else None
        )
        for label, count in [
            ("Unidades não identificadas", None),
            ("Campos geométricos ausentes", geometry_count),
            ("Quantitativos duplicados", duplicate_count),
            ("Origem não informada", sum(item["missing_origin"] for item in qualities)),
        ]:
            line = QHBoxLayout()
            item_label = QLabel("•  " + label)
            item_label.setStyleSheet("color:#46586b;")
            value = QLabel("Não apurado" if count is None else f"{count} registros")
            value.setObjectName("muted")
            line.addWidget(item_label, 1)
            line.addWidget(value)
            pending_panel.body.addLayout(line)
        middle.addWidget(pending_panel, 2)
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
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page



    def _projects_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(14)

        intro = QLabel(
            "Pesquise, filtre e acompanhe empreendimentos e contratos, com contagem das "
            "estruturas identificadas nas tabelas importadas."
        )
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.project_rows = self.store.list_projects()
        datasets = self._workspace_datasets()
        stats_by_project = {}
        for project in self.project_rows:
            linked = [item for item in datasets if item["project"]["id"] == project["id"]]
            identifiers = set()
            has_pending = False
            for dataset in linked:
                quality = self._dataset_quality(dataset)
                for record in dataset["records"]:
                    identifier = self._pick_value(
                        record["values"], "obra", "identificador", "codigo_oae",
                        "código_oae", "id_oae", "oae"
                    )
                    if self._filled(identifier):
                        identifiers.add(str(identifier).strip())
                if quality["pending_records"] > 0:
                    has_pending = True
            stats_by_project[project["id"]] = {
                "oae_count": len(identifiers), "pending": has_pending
            }

        linked_total = sum(item["oae_count"] for item in stats_by_project.values())
        execution_total = sum(
            1 for project in self.project_rows
            if "exec" in str((project.get("metadata") or {}).get(
                "stage", (project.get("metadata") or {}).get("etapa", "")
            )).casefold()
        )
        pending_total = sum(1 for item in stats_by_project.values() if item["pending"])
        layout.addWidget(self._metric_row([
            MetricCard("Projetos cadastrados", str(len(self.project_rows)), "Registros no workspace local"),
            MetricCard("OAEs identificadas", str(linked_total), "Identificadores distintos na coluna obra/código"),
            MetricCard("Em execução", str(execution_total), "Etapa explicitamente marcada como execução"),
            MetricCard("Com pendências", str(pending_total), "Projetos com tipologia ou geometria ausente", "#c58b3e"),
        ]))

        panel = Panel("Empreendimentos cadastrados", "Metadados do projeto e informações derivadas das tabelas vinculadas")
        toolbar = QHBoxLayout()
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("Buscar projeto, contrato ou responsável…")
        self.project_search.textChanged.connect(self._filter_project_rows)
        toolbar.addWidget(self.project_search, 2)
        self.project_status_filter = QComboBox()
        self.project_status_filter.addItem("Todos os status", "")
        self.project_responsible_filter = QComboBox()
        self.project_responsible_filter.addItem("Todos os responsáveis", "")
        statuses, responsibles = set(), set()
        for project in self.project_rows:
            metadata = project.get("metadata") or {}
            if metadata.get("status"):
                statuses.add(str(metadata["status"]))
            responsible = metadata.get("responsible", metadata.get("responsavel"))
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
        self.project_table.setAlternatingRowColors(True)
        self.project_table.verticalHeader().setVisible(False)
        self.project_table.setMinimumHeight(220)
        self.project_table.horizontalHeader().setStretchLastSection(True)
        for row, project in enumerate(self.project_rows):
            metadata = project.get("metadata") or {}
            stats = stats_by_project[project["id"]]
            status = metadata.get("status")
            if not status and stats["pending"]:
                status = "Pendente de validação"
            values = [
                project.get("name"),
                metadata.get("location", metadata.get("local")),
                stats["oae_count"] if stats["oae_count"] else "Não identificadas",
                metadata.get("stage", metadata.get("etapa")),
                metadata.get("responsible", metadata.get("responsavel")),
                status,
            ]
            for col, value in enumerate(values):
                self.project_table.setItem(
                    row, col, QTableWidgetItem(
                        "Não informado" if value is None or value == "" else str(value)
                    )
                )
        panel.body.addWidget(self.project_table, 1)
        layout.addWidget(panel, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll)
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
        """Display workspace-imported rows in the OAE source register without false approvals."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(12)

        intro = QLabel(
            "Consulte as estruturas identificadas nas tabelas importadas. A ficha organiza "
            "os campos disponíveis na origem sem alterar valores ou declarar validação técnica."
        )
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        source = Panel("Origem dos registros", "Selecione o projeto e a tabela importada")
        row = QHBoxLayout()
        row.addWidget(QLabel("Projeto"))
        self.bridge_project_combo = QComboBox()
        for project in self.store.list_projects():
            self.bridge_project_combo.addItem(project["name"], project["id"])
        row.addWidget(self.bridge_project_combo, 1)
        row.addWidget(QLabel("Conjunto"))
        self.bridge_dataset_combo = QComboBox()
        row.addWidget(self.bridge_dataset_combo, 2)
        source.body.addLayout(row)
        layout.addWidget(source)

        self.bridge_summary = self._metric_row([
            MetricCard("Registros de origem", "0", "Linhas da tabela selecionada"),
            MetricCard("Com tipologia", "0", "Campo de tipologia preenchido"),
            MetricCard("Com geometria", "0", "Comprimento e largura preenchidos"),
            MetricCard("Validação técnica", "Pendente", "Aprovação de engenharia não integrada", "#c58b37"),
        ])
        layout.addWidget(self.bridge_summary)

        listing = Panel("Pontes e OAEs", "Registros importados • consulta somente leitura")
        self.bridge_search = QLineEdit()
        self.bridge_search.setPlaceholderText("Buscar por identificador, tipologia ou valor de origem…")
        self.bridge_search.textChanged.connect(self._filter_bridge_records)
        listing.body.addWidget(self.bridge_search)
        self.bridge_table = QTableWidget(0, 5)
        self.bridge_table.setHorizontalHeaderLabels([
            "Identificador", "Tipologia", "Comprimento (m)", "Largura (m)", "Vãos"
        ])
        self.bridge_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bridge_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bridge_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bridge_table.setAlternatingRowColors(True)
        self.bridge_table.verticalHeader().setVisible(False)
        self.bridge_table.setMinimumHeight(230)
        self.bridge_table.horizontalHeader().setStretchLastSection(True)
        self.bridge_table.itemSelectionChanged.connect(self._show_selected_bridge_record)
        listing.body.addWidget(self.bridge_table, 1)
        layout.addWidget(listing, 2)

        detail = Panel("Ficha técnica da OAE", "Campos de origem organizados por aba • sem aprovação técnica automática")
        self.bridge_tabs = QTabWidget()
        self.bridge_tab_labels = {}
        for key, title in [
            ("identification", "Identificação"), ("geometry", "Geometria"),
            ("quantities", "Materiais e quantitativos"), ("inspections", "Inspeções"),
            ("documents", "Documentos"), ("history", "Histórico"),
        ]:
            label = QLabel("Selecione um registro para consultar os campos disponíveis.")
            label.setWordWrap(True)
            label.setObjectName("sectionIntro")
            label.setContentsMargins(12, 12, 12, 12)
            self.bridge_tab_labels[key] = label
            self.bridge_tabs.addTab(label, title)
        detail.body.addWidget(self.bridge_tabs)
        layout.addWidget(detail, 1)

        self.bridge_project_combo.currentIndexChanged.connect(self._refresh_bridge_tables)
        self.bridge_dataset_combo.currentIndexChanged.connect(self._bridge_dataset_changed)
        self._refresh_bridge_tables()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _refresh_bridge_tables(self, *_):
        if not hasattr(self, "bridge_dataset_combo"):
            return
        self.bridge_dataset_combo.blockSignals(True)
        self.bridge_dataset_combo.clear()
        project_id = self.bridge_project_combo.currentData()
        if project_id is not None:
            tables = self.store.list_tables(project_id)
            tables.sort(key=lambda item: (
                0 if item["name"].strip().casefold() == "base_limpa" else 1,
                item["name"].casefold(),
            ))
            for table in tables:
                count = len(self.store.list_records(table["id"]))
                self.bridge_dataset_combo.addItem(f'{table["name"]} · {count} registros', table["id"])
        self.bridge_dataset_combo.blockSignals(False)
        self._bridge_dataset_changed()

    def _bridge_dataset_changed(self, *_):
        if not hasattr(self, "bridge_table"):
            return
        table_id = self.bridge_dataset_combo.currentData()
        self.bridge_table.setRowCount(0)
        if table_id is None:
            self.bridge_records = []
            self._set_bridge_summary(0, 0, 0)
            for label in self.bridge_tab_labels.values():
                label.setText("Este projeto ainda não possui tabelas importadas.")
            return
        project_id = self.bridge_project_combo.currentData()
        table = next((item for item in self.store.list_tables(project_id) if item["id"] == table_id), None)
        rows = self.store.list_records(table_id)
        self.bridge_records = [
            BridgeRecord(record["values"], record["id"], None, table["name"] if table else None)
            for record in rows
        ]
        quality = self._dataset_quality({
            "records": rows,
            "columns": self.store.list_columns(table_id),
        })
        self._set_bridge_summary(quality["records"], quality["typology"], quality["geometry"])
        self.bridge_table.setRowCount(len(self.bridge_records))
        for row_index, record in enumerate(self.bridge_records):
            values = [
                self._pick_value(record.values, "obra", "identificador", "codigo_oae", "código_oae", "id_oae", "oae"),
                self._pick_value(record.values, "tipo_obra", "tipologia", "tipologia_obra", "tipo"),
                self._pick_value(record.values, "compr_obra_m", "comprimento_total_m", "comprimento_m"),
                self._pick_value(record.values, "largura_m", "largura_tabuleiro_m", "largura"),
                self._bridge_span_text(record.values),
            ]
            for col, value in enumerate(values):
                self.bridge_table.setItem(
                    row_index, col,
                    QTableWidgetItem("Não informado" if not self._filled(value) else str(value))
                )
        self.bridge_table.resizeColumnsToContents()
        if self.bridge_records:
            self.bridge_table.selectRow(0)

    def _set_bridge_summary(self, total, typology, geometry):
        old = self.bridge_summary
        parent_layout = old.parentWidget().layout()
        index = parent_layout.indexOf(old)
        parent_layout.removeWidget(old)
        old.deleteLater()
        self.bridge_summary = self._metric_row([
            MetricCard("Registros de origem", str(total), "Linhas da tabela selecionada"),
            MetricCard("Com tipologia", str(typology), "Campo de tipologia preenchido"),
            MetricCard("Com geometria", str(geometry), "Comprimento e largura preenchidos"),
            MetricCard("Validação técnica", "Pendente", "Aprovação de engenharia não integrada", "#c58b37"),
        ])
        parent_layout.insertWidget(index, self.bridge_summary)

    @staticmethod
    def _bridge_span_text(values: dict) -> str:
        direct = values.get("vão_m", values.get("vao_m", values.get("vão_total_m", values.get("vao_total_m"))))
        if direct not in (None, ""):
            return str(direct)
        return bridge_span_text(values)

    def _filter_bridge_records(self, query: str = ""):
        if not hasattr(self, "bridge_table"):
            return
        needle = query.strip().casefold()
        for row in range(self.bridge_table.rowCount()):
            text_value = " ".join(
                self.bridge_table.item(row, col).text()
                for col in range(self.bridge_table.columnCount())
                if self.bridge_table.item(row, col) is not None
            ).casefold()
            self.bridge_table.setRowHidden(row, bool(needle) and needle not in text_value)

    def _show_selected_bridge_record(self):
        if not hasattr(self, "bridge_table"):
            return
        selected = self.bridge_table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        if row >= len(self.bridge_records):
            return
        record = self.bridge_records[row]
        values = record.values

        def render(items):
            lines = []
            for label, value, *unit in items:
                shown = "Não informado" if not self._filled(value) else str(value)
                if unit and self._filled(value):
                    shown += f" {unit[0]}"
                lines.append(f"{label}: {shown}")
            return "\n".join(lines)

        identity = [
            ("Identificador", self._pick_value(values, "obra", "identificador", "codigo_oae", "código_oae", "id_oae", "oae")),
            ("Nome da estrutura", self._pick_value(values, "nome", "obra_nome", "nome_estrutura")),
            ("Projeto", self._pick_value(values, "projeto", "contrato")),
            ("Tipologia", self._pick_value(values, "tipo_obra", "tipologia", "tipologia_obra", "tipo")),
            ("Município / UF", self._pick_value(values, "municipio", "município", "local")),
            ("Rodovia / km", self._pick_value(values, "rodovia", "rodovia_km", "km")),
            ("Latitude", self._pick_value(values, "latitude")),
            ("Longitude", self._pick_value(values, "longitude")),
        ]
        geometry = [
            ("Comprimento total", self._pick_value(values, "compr_obra_m", "comprimento_total_m", "comprimento_m"), "m"),
            ("Largura do tabuleiro", self._pick_value(values, "largura_m", "largura_tabuleiro_m", "largura"), "m"),
            ("Vão", self._pick_value(values, "vão_m", "vao_m", "vão_total_m", "vao_total_m"), "m"),
            ("Vão mínimo", self._pick_value(values, "vão_min_m", "vao_min_m"), "m"),
            ("Vão máximo", self._pick_value(values, "vão_max_m", "vao_max_m"), "m"),
            ("Seção", self._pick_value(values, "seção", "secao")),
            ("Altura de viga/laje", self._pick_value(values, "hviga_laje_m"), "m"),
        ]
        quantities = [
            ("Ecm (campo da origem; unidade a confirmar)", self._pick_value(values, "em_m3_m2")),
            ("Paf", self._pick_value(values, "Paf_kg_m2"), "kg/m²"),
            ("Pap", self._pick_value(values, "Pap_kg_m2"), "kg/m²"),
            ("Af", self._pick_value(values, "Af_m2_m2"), "m²/m²"),
        ]
        self.bridge_tab_labels["identification"].setText(render(identity) + "\n\nEstado cadastral: não validado.")
        self.bridge_tab_labels["geometry"].setText(render(geometry) + "\n\nValores conforme armazenados na tabela.")
        self.bridge_tab_labels["quantities"].setText(
            render(quantities) + "\n\nDefinições, unidades e fórmulas dependem de aprovação formal da EGT."
        )
        self.bridge_tab_labels["inspections"].setText("Não há registros de inspeção vinculados a esta linha.")
        self.bridge_tab_labels["documents"].setText("Não há vínculo documental por OAE registrado para esta linha.")
        self.bridge_tab_labels["history"].setText(
            f"Projeto: {self.bridge_project_combo.currentText()}\n"
            f"Tabela: {record.source_sheet or 'não identificada'}\n"
            f"ID interno: {record.source_row}\n"
            "O nome do arquivo original e a linha da planilha não foram preservados no registro genérico."
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
            "border-radius:8px;}"        )
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
        """Scrollable analysis layout following the approved filter/results composition."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 10, 8)
        layout.setSpacing(12)

        heading = QLabel("Análise de dados de pontes e OAEs")
        heading.setMinimumHeight(34)
        heading.setStyleSheet("font-size:14pt;font-weight:700;color:#26384b;")
        subtitle = QLabel(
            "Defina intervalos, combine critérios e examine os registros importados. "
            "Indicadores técnicos aguardam validação metodológica."
        )
        subtitle.setObjectName("sectionIntro")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        scope = Panel("CONJUNTO DE DADOS", "Seleção vinculada ao repositório local")
        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("Projeto"))
        self.analysis_project = QComboBox()
        for project in self.store.list_projects():
            self.analysis_project.addItem(project["name"], project["id"])
        selectors.addWidget(self.analysis_project, 1)
        selectors.addWidget(QLabel("Conjunto"))
        self.analysis_dataset = QComboBox()
        selectors.addWidget(self.analysis_dataset, 2)
        scope.body.addLayout(selectors)
        layout.addWidget(scope)

        body = QHBoxLayout()
        body.setSpacing(14)
        filters = Panel(
            "Filtros por intervalo",
            "Escolha uma coluna numérica e informe limites opcionais."
        )
        filters.setMinimumWidth(320)
        filters.setMaximumWidth(390)
        filters.body.setSpacing(10)
        self.analysis_filter_rows = []
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for col, title in enumerate(("Campo numérico", "Mínimo", "Máximo")):
            label = QLabel(title)
            label.setMinimumHeight(24)
            label.setWordWrap(True)
            grid.addWidget(label, 0, col)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        for index in range(4):
            field = QComboBox()
            field.setMinimumWidth(0)
            field.setMinimumHeight(36)
            minimum = QLineEdit()
            minimum.setPlaceholderText("Mín.")
            minimum.setMinimumWidth(0)
            minimum.setMinimumHeight(36)
            maximum = QLineEdit()
            maximum.setPlaceholderText("Máx.")
            maximum.setMinimumWidth(0)
            maximum.setMinimumHeight(36)
            grid.addWidget(field, index + 1, 0)
            grid.addWidget(minimum, index + 1, 1)
            grid.addWidget(maximum, index + 1, 2)
            grid.setRowMinimumHeight(index + 1, 42)
            self.analysis_filter_rows.append((field, minimum, maximum))
        filters.body.addLayout(grid)

        self.analysis_search = QLineEdit()
        self.analysis_search.setPlaceholderText("Pesquisar em todos os campos…")
        self.analysis_search.setMinimumHeight(38)
        filters.body.addWidget(self.analysis_search)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        apply_button = QPushButton("Aplicar filtros")
        apply_button.setObjectName("primaryAction")
        apply_button.setMinimumHeight(40)
        apply_button.clicked.connect(self._apply_analysis_filters)
        clear_button = QPushButton("Limpar")
        clear_button.setObjectName("secondaryAction")
        clear_button.setMinimumHeight(40)
        clear_button.clicked.connect(self._clear_analysis_filters)
        buttons.addWidget(apply_button, 1)
        buttons.addWidget(clear_button)
        filters.body.addLayout(buttons)
        self.analysis_count = QLabel("Selecione um conjunto para consultar os registros.")
        self.analysis_count.setObjectName("mutedSmall")
        self.analysis_count.setMinimumHeight(34)
        self.analysis_count.setWordWrap(True)
        filters.body.addWidget(self.analysis_count)
        filters.body.addStretch(1)
        body.addWidget(filters, 0)

        right = QVBoxLayout()
        right.setSpacing(12)
        indicators = Panel(
            "Indicadores de engenharia",
            "Valores originais importados da OAE selecionada. Não são recalculados nem consolidados."
        )
        metric_grid = QGridLayout()
        metric_grid.setHorizontalSpacing(10)
        metric_grid.setVerticalSpacing(8)
        self.analysis_indicator_cards = []
        indicator_definitions = [
            ("Paf", "kg/m²", "Paf_kg_m2", 2),
            ("Pap", "kg/m²", "Pap_kg_m2", 2),
            ("Ecm* · em_m3_m2", "m³/m² · associação provisória", "em_m3_m2", 3),
            ("Af", "m²/m²", "Af_m2_m2", 2),
            ("Aço total indicativo", "kg/m²", "aço_total_indicativo_kg_m2", 2),
            ("Aço total indicativo", "kg/m³", "aço_total_indicativo_kg_m3", 2),
        ]
        for index, (name, unit, field_name, decimals) in enumerate(indicator_definitions):
            card = QFrame()
            card.setMinimumHeight(82)
            card.setStyleSheet("QFrame {background:#f4f7fa;border:1px solid #e1e7ed;border-radius:6px;}")
            box = QVBoxLayout(card)
            box.setContentsMargins(9, 7, 9, 7)
            label = QLabel(name)
            label.setObjectName("mutedSmall")
            label.setWordWrap(True)
            value = QLabel("Selecione uma OAE")
            value.setStyleSheet("font-size:12pt;font-weight:700;color:#294b67;")
            unit_label = QLabel(unit)
            unit_label.setObjectName("mutedSmall")
            box.addWidget(label)
            box.addWidget(value)
            box.addWidget(unit_label)
            metric_grid.addWidget(card, index // 3, index % 3)
            self.analysis_indicator_cards.append((value, field_name, decimals))
        indicators.body.addLayout(metric_grid)
        indicator_status = QLabel(
            "Valor importado — validação técnica pendente. Ecm* é uma associação provisória "
            "ao campo em_m3_m2 e requer confirmação da EGT."
        )
        indicator_status.setObjectName("mutedSmall")
        indicator_status.setWordWrap(True)
        indicators.body.addWidget(indicator_status)
        right.addWidget(indicators)

        results = Panel(
            "Resultados da seleção",
            "Linhas da tabela importada • use as barras para percorrer colunas e registros."
        )
        self.analysis_results_count = QLabel("Nenhum conjunto selecionado.")
        self.analysis_results_count.setObjectName("mutedSmall")
        results.body.addWidget(self.analysis_results_count)
        self.analysis_table = QTableWidget(0, 0)
        self.analysis_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.analysis_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setWordWrap(False)
        self.analysis_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.analysis_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.analysis_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.analysis_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.analysis_table.verticalHeader().setVisible(False)
        self.analysis_table.verticalHeader().setDefaultSectionSize(34)
        self.analysis_table.horizontalHeader().setDefaultSectionSize(145)
        self.analysis_table.horizontalHeader().setMinimumSectionSize(105)
        self.analysis_table.horizontalHeader().setStretchLastSection(False)
        self.analysis_table.setMinimumHeight(350)
        results.body.addWidget(self.analysis_table, 1)
        right.addWidget(results, 1)
        body.addLayout(right, 1)
        layout.addLayout(body, 1)

        note = QLabel(
            "Integridade metodológica: os filtros consultam os valores armazenados sem alterar a origem. "
            "Paf, Pap, Ecm, Af e aço permanecem sem cálculo até validação formal de definições, "
            "unidades e fórmulas."
        )
        note.setWordWrap(True)
        note.setStyleSheet("background:#fff5e5;color:#93621f;padding:10px;border-radius:6px;")
        layout.addWidget(note)

        self.analysis_project.currentIndexChanged.connect(self._refresh_analysis_tables)
        self.analysis_dataset.currentIndexChanged.connect(self._analysis_dataset_changed)
        self.analysis_search.textChanged.connect(self._apply_analysis_filters)
        self.analysis_table.itemSelectionChanged.connect(self._analysis_selection_changed)
        self._refresh_analysis_tables()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _refresh_analysis_tables(self, *_):
        if not hasattr(self, "analysis_dataset"):
            return
        self.analysis_dataset.blockSignals(True)
        self.analysis_dataset.clear()
        project_id = self.analysis_project.currentData()
        if project_id is not None:
            for table in self.store.list_tables(project_id):
                count = len(self.store.list_records(table["id"]))
                self.analysis_dataset.addItem(f'{table["name"]} · {count} registros', table["id"])
        self.analysis_dataset.blockSignals(False)
        self._analysis_dataset_changed()

    def _analysis_dataset_changed(self, *_):
        if not hasattr(self, "analysis_dataset"):
            return
        table_id = self.analysis_dataset.currentData()
        for field, minimum, maximum in self.analysis_filter_rows:
            field.blockSignals(True)
            field.clear()
            field.addItem("Selecionar campo", None)
        if table_id is None:
            self.analysis_columns = []
            self.analysis_records = []
            self.analysis_filtered_records = []
            self.analysis_count.setText("Este projeto ainda não possui tabelas importadas.")
            self.analysis_results_count.setText("Nenhum conjunto selecionado.")
            self.analysis_table.clear()
            self.analysis_table.setRowCount(0)
            self.analysis_table.setColumnCount(0)
            self._update_analysis_indicators(None)
            for field, minimum, maximum in self.analysis_filter_rows:
                field.blockSignals(False)
                minimum.clear()
                maximum.clear()
            return

        self.analysis_columns = self.store.list_columns(table_id)
        self.analysis_records = self.store.list_records(table_id)
        unit_tokens = ("_m", "m²", "m2", "m³", "m3", "_kg", "kg_", "mm", "cm")
        excluded = {"obra", "data", "id", "identificador", "seção", "secao"}
        numeric = [
            column for column in self.analysis_columns
            if column.get("data_type") in ("integer", "decimal")
            or (
                column["name"].casefold() not in excluded
                and any(token in column["name"].casefold() for token in unit_tokens)
            )
        ]
        preferred = ("compr_obra_m", "largura_m", "vão_m", "vao_m", "hviga_laje_m", "em_m3_m2")
        for row_index, (field, minimum, maximum) in enumerate(self.analysis_filter_rows):
            for column in numeric:
                field.addItem(column["name"], column["name"])
            if row_index < len(preferred):
                index = field.findData(preferred[row_index])
                if index > 0:
                    field.setCurrentIndex(index)
            field.blockSignals(False)
            minimum.clear()
            maximum.clear()
        self._apply_analysis_filters()

    @staticmethod
    def _analysis_number(value):
        if value is None or isinstance(value, bool) or str(value).strip() == "":
            return None
        try:
            raw = str(value).strip().replace(" ", "")
            if "," in raw and "." in raw:
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", ".")
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _clear_analysis_filters(self):
        for field, minimum, maximum in self.analysis_filter_rows:
            field.setCurrentIndex(0)
            minimum.clear()
            maximum.clear()
        self.analysis_search.clear()
        self._apply_analysis_filters()

    def _apply_analysis_filters(self, *_):
        if not hasattr(self, "analysis_table"):
            return
        table_id = self.analysis_dataset.currentData()
        if table_id is None:
            return
        active_ranges = []
        for field, minimum, maximum in self.analysis_filter_rows:
            name = field.currentData()
            low_text, high_text = minimum.text().strip(), maximum.text().strip()
            if not name or (not low_text and not high_text):
                continue
            low = self._analysis_number(low_text) if low_text else None
            high = self._analysis_number(high_text) if high_text else None
            if (low_text and low is None) or (high_text and high is None):
                message = "Use limites numéricos válidos. Exemplo: 12,5."
                self.analysis_count.setText(message)
                self.analysis_results_count.setText(message)
                return
            if low is not None and high is not None and low > high:
                message = f"O mínimo de '{name}' não pode ser maior que o máximo."
                self.analysis_count.setText(message)
                self.analysis_results_count.setText(message)
                return
            active_ranges.append((name, low, high))

        needle = self.analysis_search.text().strip().casefold()
        selected = []
        records = self.analysis_records
        for record in records:
            values = record["values"]
            keep = True
            for name, low, high in active_ranges:
                number = self._analysis_number(values.get(name))
                if number is None or (low is not None and number < low) or (high is not None and number > high):
                    keep = False
                    break
            if keep and needle:
                keep = needle in " ".join(
                    str(value) for value in values.values() if value is not None
                ).casefold()
            if keep:
                selected.append(record)

        headers = [column["name"] for column in self.analysis_columns]
        self.analysis_filtered_records = selected
        self.analysis_table.setUpdatesEnabled(False)
        self.analysis_table.clear()
        self.analysis_table.setColumnCount(len(headers))
        self.analysis_table.setHorizontalHeaderLabels(headers)
        self.analysis_table.setRowCount(len(selected))
        for row, record in enumerate(selected):
            for col, name in enumerate(headers):
                value = record["values"].get(name)
                self.analysis_table.setItem(
                    row, col, QTableWidgetItem("—" if value is None else str(value))
                )
        header = self.analysis_table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.analysis_table.setColumnWidth(col, 145)
        self.analysis_table.setUpdatesEnabled(True)
        message = (
            f"{len(selected)} de {len(records)} registros exibidos"
            + (f" · {len(active_ranges)} intervalo(s) ativo(s)" if active_ranges else "")
            + (" · pesquisa textual ativa" if needle else "")
        )
        self.analysis_count.setText(message)
        self.analysis_results_count.setText(message)
        if len(selected) == 1:
            self.analysis_table.selectRow(0)
        else:
            self._update_analysis_indicators(None)

    def _analysis_selection_changed(self):
        if not hasattr(self, "analysis_table"):
            return
        selected_rows = self.analysis_table.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            self._update_analysis_indicators(None)
            return
        row = selected_rows[0].row()
        records = getattr(self, "analysis_filtered_records", [])
        if row < 0 or row >= len(records):
            self._update_analysis_indicators(None)
            return
        self._update_analysis_indicators(records[row]["values"])

    def _update_analysis_indicators(self, values):
        if not hasattr(self, "analysis_indicator_cards"):
            return
        for value_label, field_name, decimals in self.analysis_indicator_cards:
            raw_value = self._pick_value(values, field_name) if values is not None else None
            number = self._analysis_number(raw_value)
            if raw_value is None or str(raw_value).strip() == "":
                display = "Dado ausente" if values is not None else "Selecione uma OAE"
            elif number is None:
                display = str(raw_value)
            else:
                display = f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            value_label.setText(display)

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
            "Consulte arquivos indexados neste dispositivo. O catálogo preserva o caminho, "            "o hash e o resultado da extração; indexação não significa aprovação técnica."
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
            self, "Renomear tabela", "Novo nome:", text=current_name        )
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
        """Refresh all modules whose content depends on imported workspace records."""
        current_widget = self.stack.currentWidget()
        current_name = next(
            (name for name, widget in self.pages.items() if widget is current_widget),
            "Visão geral",
        )
        builders = {
            "Visão geral": self._overview_page,
            "Projetos e obras": self._projects_page,
            "Pontes e OAEs": self._bridges_page,
            "Importar dados": self._import_page,
            "Análise de engenharia": self._analysis_page,
        }
        for name, builder in builders.items():
            old = self.pages.get(name)
            if old is None:
                continue
            index = self.stack.indexOf(old)
            self.stack.removeWidget(old)
            old.deleteLater()
            new_page = builder()
            self.pages[name] = new_page
            self.stack.insertWidget(index, new_page)
        self.navigate(current_name)
