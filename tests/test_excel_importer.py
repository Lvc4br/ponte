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
