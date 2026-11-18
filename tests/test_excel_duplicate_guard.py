import pytest

from app.core.models import BridgeRecord
from app.data.dataset_store import DatasetStore


def test_same_excel_fingerprint_is_rejected_after_reopening_store(tmp_path):
    database = tmp_path / "records.sqlite3"
    fingerprint = "a" * 64
    records = [BridgeRecord({"obra": 1, "vão_m": "20"}, 2)]

    store = DatasetStore(database)
    assert store.append_imported_file(
        fingerprint, "pontes.xlsx", "Dados", records
    ) == 1
    assert store.has_imported_file(fingerprint)

    reopened_store = DatasetStore(database)
    assert reopened_store.has_imported_file(fingerprint)
    with pytest.raises(ValueError, match="já foi importado"):
        reopened_store.append_imported_file(
            fingerprint, "pontes-renomeado.xlsx", "Dados", records
        )

    assert len(reopened_store.load()) == 1


def test_different_excel_fingerprints_can_be_imported(tmp_path):
    store = DatasetStore(tmp_path / "records.sqlite3")
    first = BridgeRecord({"obra": 1}, 2)
    second = BridgeRecord({"obra": 2}, 3)

    assert store.append_imported_file("a" * 64, "um.xlsx", "Dados", [first]) == 1
    assert store.append_imported_file("b" * 64, "dois.xlsx", "Dados", [second]) == 1
    assert len(store.load()) == 2
