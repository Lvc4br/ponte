from pathlib import Path
from app.data.excel_reader import read_excel_records
class ExcelRepository:
    def __init__(self): self.records=[]; self.source=None
    def load(self, path, sheet_name='Base_limpa'):
        self.records=read_excel_records(path, sheet_name)
        self.source=Path(path)
        return self.records
