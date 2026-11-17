from pathlib import Path

from openpyxl import load_workbook

from app.core.models import BridgeRecord


HEADER_ALIASES = {
    "vão_m": "vao_m",
    "vao_m": "vao_m",
    "vão": "vao_m",
    "vão_min_m": "vao_min_m",
    "vão_max_m": "vao_max_m",
    "largura": "largura_m",
    "comprimento": "compr_obra_m",
}


def read_excel(path, sheet_name=None):
    """Read an .xlsx worksheet without coercing source values or dropping rows."""
    path = Path(path)
    if path.suffix.casefold() != ".xlsx":
        raise ValueError("Por enquanto, o importador aceita arquivos .xlsx.")
    if not path.is_file():
        raise FileNotFoundError(path)

    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        if sheet_name is None:
            sheet_name = workbook.sheetnames[0]
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"A aba '{sheet_name}' não existe no arquivo.")
        worksheet = workbook[sheet_name]
        rows = worksheet.iter_rows(values_only=True)
        header_row = next(rows, None)
        if not header_row:
            raise ValueError("A planilha está vazia.")
        headers = []
        for index, value in enumerate(header_row, start=1):
            name = str(value).strip() if value is not None else ""
            headers.append(name or f"coluna_{index}")
        if len(set(headers)) != len(headers):
            raise ValueError("Existem cabeçalhos repetidos; renomeie-os antes de importar.")

        records = []
        for row_number, row in enumerate(rows, start=2):
            if not any(value is not None for value in row):
                continue
            values = {}
            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else None
                canonical = HEADER_ALIASES.get(header.casefold(), header)
                values[header] = value
                if canonical != header:
                    values[canonical] = value
            records.append(BridgeRecord(values, row_number))
        if not records:
            raise ValueError("A aba não contém registros abaixo do cabeçalho.")
        return records
    finally:
        workbook.close()
