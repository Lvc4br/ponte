from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

from app.core.analytics import RATE_FIELDS, summarize_rates
from app.core.matching import missing_criteria_fields
from app.core.models import NumericRange, SearchCriteria
from app.core.validation import format_display_value, parse_input_number
from app.data.excel_importer import read_excel
from app.data.repository import SQLRepository
from app.services.search_service import SearchService


RATE_LABELS = {
    "em_m3_m2": "Concreto (em_m3_m2)",
    "Paf_kg_m2": "Paf_kg_m2",
    "Pap_kg_m2": "Pap_kg_m2",
    "Af_m2_m2": "Af_m2_m2",
}


def _pt_number(value):
    if value is None:
        return "—"
    return f"{value:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Consulta de Taxas de Pontes")
        self.resize(1320, 850)
        self.repo = SQLRepository()
        self.service = SearchService()
        self.results = []
        self._build()
        self.load_sql()

    def _build(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        title = QLabel("Consulta de taxas de pontes")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#173b57")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "Referências para consulta. O sistema não realiza dimensionamento "
            "nem validação estrutural."
        ))

        bar = QHBoxLayout()
        self.actions_button = QToolButton()
        self.actions_button.setText("⋮")
        self.actions_button.setToolTip("Ações da base de dados")
        self.actions_button.setAccessibleName("Ações da base de dados")
        self.actions_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        actions_menu = QMenu(self.actions_button)
        reload_action = actions_menu.addAction("Recarregar arquivo SQL")
        reload_action.triggered.connect(self.load_sql)
        import_action = actions_menu.addAction("Adicionar registros do Excel")
        import_action.triggered.connect(self.import_excel)
        delete_action = actions_menu.addAction("Excluir selecionados")
        delete_action.triggered.connect(self.delete_selected)
        self.actions_button.setMenu(actions_menu)
        bar.addWidget(self.actions_button)
        self.status = QLabel("Carregando base SQL...")
        bar.addWidget(self.status, 1)
        layout.addLayout(bar)

        group = QGroupBox("Parâmetros de pesquisa")
        form = QFormLayout(group)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Ex.: Ponte (opcional)")
        form.addRow("Tipo de obra", self.type_input)
        self.fields = {}
        for key, label in [
            ("width", "Largura (m)"),
            ("span", "Vão (m)"),
            ("total_length", "Comprimento total (m)"),
        ]:
            pair = QWidget()
            row = QHBoxLayout(pair)
            row.setContentsMargins(0, 0, 0, 0)
            low, high = QLineEdit(), QLineEdit()
            low.setPlaceholderText("Mínimo")
            high.setPlaceholderText("Máximo")
            row.addWidget(low)
            row.addWidget(high)
            form.addRow(label, pair)
            self.fields[key] = (low, high)
        layout.addWidget(group)

        buttons = QHBoxLayout()
        for label, slot in [
            ("Pesquisar", self.search),
            ("Limpar filtros", self.clear),
        ]:
            button = QPushButton(label)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

        summary_group = QGroupBox("Resumo da consulta")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_headline = QLabel("Carregue a base para consultar.")
        self.summary_headline.setStyleSheet(
            "font-size:15px;font-weight:700;color:#173b57"
        )
        self.summary_headline.setWordWrap(True)
        summary_layout.addWidget(self.summary_headline)
        self.summary_detail = QLabel("")
        self.summary_detail.setWordWrap(True)
        summary_layout.addWidget(self.summary_detail)

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
        summary_layout.addWidget(self.rate_table)
        note = QLabel(
            "Estatísticas calculadas por registro, não por obra única. "
            "Valores ausentes e textos não numéricos são excluídos apenas do "
            "cálculo daquele indicador. A interpretação técnica de Paf, Pap e Af "
            "depende da documentação da fonte."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#596579;font-size:11px")
        summary_layout.addWidget(note)
        layout.addWidget(summary_group)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(
            "QMainWindow{background:#f5f7fb} "
            "QGroupBox{font-weight:600;border:1px solid #d8dee9;"
            "border-radius:8px;margin-top:8px;padding:10px} "
            "QLineEdit,QTableWidget{background:white;border:1px solid "
            "#d8dee9;border-radius:5px;padding:6px} "
            "QPushButton{background:#173b57;color:white;border:0;"
            "border-radius:6px;padding:9px 14px} "
            "QPushButton:hover{background:#245878}"
        )

    def load_sql(self):
        try:
            records = self.repo.load()
            self.results = records
            self.show_records(records)
            source_label = (
                Path(self.repo.source).name if self.repo.source
                else "Base local salva"
            )
            self.status.setText(
                f"{source_label} — {len(records)} registros ativos"
            )
        except Exception as exc:
            self.results = self.repo.records
            self.show_records(self.results)
            self.status.setText("Base SQL não carregada")
            QMessageBox.warning(
                self, "Não foi possível carregar a base SQL", str(exc)
            )

    def import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar planilha Excel", "",
            "Planilhas Excel (*.xlsx)"
        )
        if not path:
            return
        try:
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
                f"Arquivo: {Path(path).name}\nAba: {sheet}\n"
                f"Novos registros: {len(incoming)}\n\n"
                f"Prévia das primeiras linhas:\n{preview}{more}\n\n"
                "Os registros serão ADICIONADOS à base atual. "
                "Nenhum registro existente será substituído ou deduplicado.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            count = self.repo.add_records(incoming)
            self.results = self.repo.records
            self.show_records(self.results)
            self.status.setText(
                f"{count} registro(s) adicionados — {len(self.repo.records)} ativos"
            )
            QMessageBox.information(
                self, "Importação concluída",
                f"{count} registro(s) adicionados com sucesso. "
                "A base foi salva localmente e continuará disponível ao reabrir o aplicativo."
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
                "Selecione uma ou mais linhas na tabela antes de excluir."
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
            self.show_records(self.results)
            self.status.setText(
                f"{deleted} registro(s) excluídos — {len(self.repo.records)} ativos"
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
        if not self.repo.records:
            QMessageBox.information(
                self, "Base necessária",
                "Coloque database/ponte.sql na pasta do aplicativo e cadastre os dados autorizados."
            )
            return
        try:
            criteria = self.criteria()
            self.results = self.service.search(self.repo.records, criteria)
            self.show_records(self.results, criteria)
            self.status.setText(f"{len(self.results)} registro(s) retornado(s)")
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
        self.results = self.repo.records
        self.show_records(self.results)
        self.status.setText(f"{len(self.results)} registros carregados")

    def _show_summary(self, records, criteria=None):
        source_count = len(self.repo.records)
        result_count = len(records)
        if criteria is None:
            self.summary_headline.setText(
                f"Base carregada: {source_count} registros."
            )
            self.summary_detail.setText(
                "Nenhum filtro ativo. As estatísticas abaixo consideram todos os registros."
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
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
