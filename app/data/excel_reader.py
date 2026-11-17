from pathlib import Path
import pandas as pd
from app.core.models import BridgeRecord
from app.data.column_mapper import normalize_header

def read_excel_records(path, sheet_name='Base_limpa', header_row=1):
    source = Path(path)
    if not source.exists(): raise FileNotFoundError(source)
    frame = pd.read_excel(source, sheet_name=sheet_name, header=header_row, dtype=object).dropna(how='all')
    records=[]
    for idx,row in frame.iterrows():
        values={}
        for col,value in row.items():
            canonical=normalize_header(col)
            values[canonical] = None if pd.isna(value) else value
        records.append(BridgeRecord(values, int(idx)+header_row+1))
    return records
