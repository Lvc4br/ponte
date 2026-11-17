from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QFileDialog,QTableWidget,QTableWidgetItem,QMessageBox,QGroupBox,QFormLayout
from app.data.repository import ExcelRepository
from app.core.models import NumericRange,SearchCriteria
from app.core.validation import parse_number
from app.services.search_service import SearchService
from app.services.export_service import export_records

class MainWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('ConsultaTaxasPontes'); self.resize(1150,700); self.repo=ExcelRepository(); self.service=SearchService(); self.results=[]; self._build()
 def _build(self):
  root=QWidget(); layout=QVBoxLayout(root)
  title=QLabel('Consulta de taxas históricas de pontes'); title.setStyleSheet('font-size:22px;font-weight:700;color:#173b57')
  layout.addWidget(title); layout.addWidget(QLabel('Pesquise obras de referência por largura, vão e comprimento total.'))
  bar=QHBoxLayout(); load=QPushButton('Abrir planilha Excel'); load.clicked.connect(self.load_excel); bar.addWidget(load); self.status=QLabel('Nenhuma planilha carregada'); bar.addWidget(self.status,1); layout.addLayout(bar)
  group=QGroupBox('Intervalos de pesquisa (m)'); form=QFormLayout(group); self.fields={}
  for key,label in [('width','Largura'),('span','Vão'),('total_length','Comprimento total')]:
   pair=QWidget(); row=QHBoxLayout(pair); row.setContentsMargins(0,0,0,0); lo=QLineEdit(); hi=QLineEdit(); lo.setPlaceholderText('Mínimo'); hi.setPlaceholderText('Máximo'); row.addWidget(lo); row.addWidget(hi); form.addRow(label,pair); self.fields[key]=(lo,hi)
  layout.addWidget(group)
  buttons=QHBoxLayout()
  for label,slot in [('Pesquisar',self.search),('Limpar filtros',self.clear),('Exportar resultados',self.export)]:
   b=QPushButton(label); b.clicked.connect(slot); buttons.addWidget(b)
  buttons.addStretch(); layout.addLayout(buttons)
  self.table=QTableWidget(); self.table.setAlternatingRowColors(True); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); layout.addWidget(self.table,1)
  self.setCentralWidget(root); self.setStyleSheet('QMainWindow{background:#f5f7fb} QGroupBox{font-weight:600;border:1px solid #d8dee9;border-radius:8px;margin-top:8px;padding:10px} QLineEdit,QTableWidget{background:white;border:1px solid #d8dee9;border-radius:5px;padding:6px} QPushButton{background:#173b57;color:white;border:0;border-radius:6px;padding:9px 14px} QPushButton:hover{background:#245878}')
 def load_excel(self):
  path,_=QFileDialog.getOpenFileName(self,'Selecionar planilha','','Excel (*.xlsx *.xls)')
  if not path:return
  try:
   records=self.repo.load(path); self.results=records; self.status.setText(f'{Path(path).name} — {len(records)} obras carregadas'); self.show_records(records)
  except Exception as exc: QMessageBox.critical(self,'Erro ao abrir planilha',str(exc))
 def criteria(self):
  data={}
  for key,(lo,hi) in self.fields.items():
   a=parse_number(lo.text()) if lo.text().strip() else None; b=parse_number(hi.text()) if hi.text().strip() else None
   if a is not None and b is not None and a>b: raise ValueError('O mínimo não pode ser maior que o máximo.')
   data[key]=NumericRange(a if a is not None else float('-inf'),b if b is not None else float('inf')) if a is not None or b is not None else None
  return SearchCriteria(**data)
 def search(self):
  if not self.repo.records: QMessageBox.information(self,'Planilha necessária','Abra uma planilha primeiro.'); return
  try:
   self.results=self.service.search(self.repo.records,self.criteria()); self.show_records(self.results); self.status.setText(f'{len(self.results)} resultado(s)')
  except ValueError as exc: QMessageBox.warning(self,'Filtros inválidos',str(exc))
 def clear(self):
  for pair in self.fields.values(): pair[0].clear(); pair[1].clear()
  self.results=self.repo.records; self.show_records(self.results)
 def show_records(self,records):
  cols=list(dict.fromkeys(k for r in records for k in r.values)); self.table.clear(); self.table.setRowCount(len(records)); self.table.setColumnCount(len(cols)); self.table.setHorizontalHeaderLabels(cols)
  for i,r in enumerate(records):
   for j,k in enumerate(cols): self.table.setItem(i,j,QTableWidgetItem('' if r.get(k) is None else str(r.get(k))))
  self.table.resizeColumnsToContents()
 def export(self):
  if not self.results: QMessageBox.information(self,'Sem resultados','Não há resultados para exportar.'); return
  path,_=QFileDialog.getSaveFileName(self,'Exportar resultados','resultados_pontes.xlsx','Excel (*.xlsx)')
  if path:
   try: export_records(self.results,path); QMessageBox.information(self,'Concluído',f'Arquivo salvo em:\n{path}')
   except Exception as exc: QMessageBox.critical(self,'Erro na exportação',str(exc))
