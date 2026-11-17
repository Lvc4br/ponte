from openpyxl import Workbook

from app.data.excel_importer import read_excel
from app.data.dataset_store import DatasetStore
from app.core.models import BridgeRecord


def test_excel_import_preserves_interval_and_blank_fields(tmp_path):
    path = tmp_path / "pontes.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["obra", "largura_m", "vão_m", "compr_obra_m", "seção"])
    sheet.append([4, "13,58", "41,25 - 41,80", 2118.2, "I"])
    sheet.append([5, None, "39.9", 900, None])
    workbook.save(path)

    records = read_excel(path)
    assert len(records) == 2
    assert records[0].get("vão_m") == "41,25 - 41,80"
    assert records[0].get("largura_m") == "13,58"
    assert records[1].get("largura_m") is None


def test_dataset_store_add_load_and_delete(tmp_path):
    store = DatasetStore(tmp_path / "records.sqlite3")
    store.append([
        BridgeRecord({"obra": 1, "vão_m": "20"}, 2),
        BridgeRecord({"obra": 2, "vão_m": "30"}, 3),
    ])
    records = store.load()
    assert len(records) == 2
    assert store.delete([records[0].source_row]) == 1
    remaining = store.load()
    assert len(remaining) == 1
    assert remaining[0].get("obra") == 2


def test_excel_import_normalizes_common_engineering_headers(tmp_path):
    path = tmp_path / "cabecalhos.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "Largura (m)", "Vão (m)", "Comprimento total (m)", "Tipo de obra"
    ])
    sheet.append([12.5, "41,25 - 41,80", 120, "Ponte"])
    workbook.save(path)

    record = read_excel(path)[0]
    assert record.get("Largura (m)") == 12.5
    assert record.get("largura_m") == 12.5
    assert record.get("vao_m") == "41,25 - 41,80"
    assert record.get("compr_obra_m") == 120
    assert record.get("tipo_obra") == "Ponte"


def test_excel_import_rejects_duplicate_canonical_columns(tmp_path):
    import pytest

    path = tmp_path / "colunas_duplicadas.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["largura_m", "Largura (m)"])
    sheet.append([12, 13])
    workbook.save(path)

    with pytest.raises(ValueError, match="Mais de uma coluna"):
        read_excel(path)



def test_imported_excel_records_can_be_filtered_by_dimensions(tmp_path):
    from app.core.matching import filter_records
    from app.core.models import NumericRange, SearchCriteria

    path = tmp_path / "pesquisa.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Largura (m)", "Vão (m)", "Comprimento total (m)"])
    sheet.append([12.5, "41,25 - 41,80", 120])
    sheet.append([8.0, "20,0", 45])
    workbook.save(path)

    records = read_excel(path)
    result = filter_records(
        records,
        SearchCriteria(
            width=NumericRange(12, 13),
            span=NumericRange(41.5, 42),
            total_length=NumericRange(100, 130),
        ),
    )
    assert len(result) == 1
    assert result[0].get("largura_m") == 12.5
