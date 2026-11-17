from pathlib import Path
import re
import unicodedata

from openpyxl import load_workbook

from app.core.models import BridgeRecord


# Nomes de origem conhecidos. As chaves são normalizadas antes da comparação.
HEADER_ALIASES = {
    "obra": "obra", "numero da obra": "obra", "n obra": "obra", "data": "data",
    "vão_m": "vao_m", "vao_m": "vao_m", "vão": "vao_m", "vão (m)": "vao_m",
    "vao (m)": "vao_m", "vão_min_m": "vao_min_m", "vão min m": "vao_min_m",
    "vão mínimo (m)": "vao_min_m", "vao_min_m": "vao_min_m",
    "vão_max_m": "vao_max_m", "vão max m": "vao_max_m",
    "vão máximo (m)": "vao_max_m", "vao_max_m": "vao_max_m",
    "largura": "largura_m", "largura_m": "largura_m", "largura (m)": "largura_m",
    "comprimento": "compr_obra_m", "compr_obra_m": "compr_obra_m",
    "comprimento total": "compr_obra_m", "comprimento total (m)": "compr_obra_m",
    "compr obra": "compr_obra_m", "compr obra m": "compr_obra_m",
    "compr obra (m)": "compr_obra_m", "comprimento da obra m": "compr_obra_m",
    "seção": "seção", "secao": "seção", "tipo de viga": "seção",
    "hviga laje m": "hviga_laje_m", "h viga laje m": "hviga_laje_m",
    "em_m3_m2": "em_m3_m2", "em m3 m2": "em_m3_m2",
    "taxa de concreto": "em_m3_m2",
    "paf_kg_m2": "Paf_kg_m2", "paf kg m2": "Paf_kg_m2",
    "pap_kg_m2": "Pap_kg_m2", "pap kg m2": "Pap_kg_m2",
    "af_m2_m2": "Af_m2_m2", "af m2 m2": "Af_m2_m2",
    "tipo de obra": "tipo_obra", "tipo_obra": "tipo_obra",
}


def _normalize_header(value):
    text = unicodedata.normalize("NFKD", str(value).strip().casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


_NORMALIZED_ALIASES = {
    _normalize_header(source): target
    for source, target in HEADER_ALIASES.items()
}


def _find_header_row(rows, scan_limit=30):
    """Find the most likely header among the first rows, tolerating title rows."""
    best_index = None
    best_score = 0
    for index, row in enumerate(rows[:scan_limit]):
        recognized = {
            _NORMALIZED_ALIASES[_normalize_header(value)]
            for value in row
            if value is not None
            and _normalize_header(value) in _NORMALIZED_ALIASES
        }
        if len(recognized) > best_score:
            best_index, best_score = index, len(recognized)
    if best_index is None or best_score < 2:
        raise ValueError(
            "Não foi possível identificar o cabeçalho da planilha. "
            "Verifique se há nomes de colunas como largura, vão, comprimento "
            "ou indicadores técnicos."
        )
    return best_index

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
        rows = list(worksheet.iter_rows(values_only=True))
        if not rows:
            raise ValueError("A planilha está vazia.")
        header_index = _find_header_row(rows)
        header_row = rows[header_index]
        headers = []
        canonical_columns = {}
        for index, value in enumerate(header_row, start=1):
            name = str(value).strip() if value is not None else ""
            name = name or f"coluna_{index}"
            headers.append(name)
            canonical = _NORMALIZED_ALIASES.get(_normalize_header(name), name)
            if canonical in canonical_columns:
                raise ValueError(
                    f"Mais de uma coluna representa '{canonical}'. "
                    "Mantenha apenas uma coluna equivalente ou renomeie os cabeçalhos."
                )
            canonical_columns[canonical] = name
        if len(set(headers)) != len(headers):
            raise ValueError("Existem cabeçalhos repetidos; renomeie-os antes de importar.")

        records = []
        for row_number, row in enumerate(rows[header_index + 1:], start=header_index + 2):
            if not any(value is not None for value in row):
                continue
            values = {}
            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else None
                canonical = _NORMALIZED_ALIASES.get(
                    _normalize_header(header), header
                )
                values[header] = value
                if canonical != header:
                    values[canonical] = value
            records.append(BridgeRecord(values, row_number))
        if not records:
            raise ValueError("A aba não contém registros abaixo do cabeçalho.")
        return records
    finally:
        workbook.close()
