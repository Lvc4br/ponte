from pathlib import Path

from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.core.models import NumericRange, SearchCriteria
from app.core.validation import parse_input_number
from app.data.repository import SQLRepository
from app.services.search_service import SearchService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ConsultaTaxasPontes")
        self.resize(1150, 700)
        self.repo = SQLRepository()
        self.service = SearchService()
        self.results = []
        self._build()
        self.load_sql()

    def _build(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        title = QLabel("Consulta de taxas históricas de pontes")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#173b57")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "Informe o tipo de obra e as dimensões para localizar referências históricas."
        ))

        bar = QHBoxLayout()
        reload_button = QPushButton("Recarregar arquivo SQL")
        reload_button.clicked.connect(self.load_sql)
        bar.addWidget(reload_button)
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

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
            self.status.setText(
                f"{Path(self.repo.source).name} — {len(records)} obras carregadas"
            )
        except Exception as exc:
            self.results = []
            self.show_records([])
            self.status.setText("Base SQL não carregada")
            QMessageBox.warning(self, "Não foi possível carregar a base SQL", str(exc))

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
                "Crie database/ponte.sql a partir de database/ponte.sql.example e cadastre as obras."
            )
            return
        try:
            self.results = self.service.search(self.repo.records, self.criteria())
            self.show_records(self.results)
            self.status.setText(f"{len(self.results)} obra(s) compatível(is)")
        except ValueError as exc:
            QMessageBox.warning(self, "Filtros inválidos", str(exc))

    def clear(self):
        self.type_input.clear()
        for low, high in self.fields.values():
            low.clear()
            high.clear()
        self.results = self.repo.records
        self.show_records(self.results)
        self.status.setText(f"{len(self.results)} obras carregadas")

    def show_records(self, records):
        columns = list(dict.fromkeys(
            key for record in records for key in record.values
        ))
        self.table.clear()
        self.table.setRowCount(len(records))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        for row_index, record in enumerate(records):
            for column_index, key in enumerate(columns):
                value = record.get(key)
                self.table.setItem(
                    row_index, column_index,
                    QTableWidgetItem("" if value is None else str(value)),
                )
        self.table.resizeColumnsToContents()
