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


def test_imported_sheet_origin_survives_reopening_store(tmp_path):
    database = tmp_path / "records.sqlite3"
    store = DatasetStore(database)
    record = BridgeRecord({"obra": "Ponte A"}, 8)

    store.append_imported_file("c" * 64, "pontes.xlsx", "Estruturas", [record])
    loaded = DatasetStore(database).load()

    assert len(loaded) == 1
    assert loaded[0].source_file == "pontes.xlsx"
    assert loaded[0].source_sheet == "Estruturas"
    assert loaded[0].values == {"obra": "Ponte A"}


def test_existing_records_table_is_migrated_without_losing_rows(tmp_path):
    import sqlite3

    database = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE records (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO records(payload) VALUES (?)",
            ('{"obra": "Registro antigo"}',),
        )

    loaded = DatasetStore(database).load()

    assert len(loaded) == 1
    assert loaded[0].values["obra"] == "Registro antigo"
    assert loaded[0].source_file is None
    assert loaded[0].source_sheet is None
