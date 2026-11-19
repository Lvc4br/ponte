import pytest

from app.workspace.batch_edit import BatchEditError, SpreadsheetBatchEditor
from app.workspace.store import WorkspaceStore


def make_table(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project_id = store.create_project("Teste")
    table_id = store.create_table(project_id, "Estruturas")
    store.add_column(table_id, "nome", "text", required=True)
    store.add_column(table_id, "largura", "decimal")
    first = store.insert_record(table_id, {"nome": "A", "largura": 8.0})
    second = store.insert_record(table_id, {"nome": "B", "largura": 10.0})
    return store, table_id, first, second


def test_batch_edit_updates_multiple_rows_and_returns_undo_snapshots(tmp_path):
    store, table_id, first, second = make_table(tmp_path)
    editor = SpreadsheetBatchEditor(store)
    result = editor.update_records(table_id, {
        first: {"largura": 8.5},
        second: {"largura": 10.5},
    })
    assert result.updated_count == 2
    rows = store.list_records(table_id)
    assert [row["values"]["largura"] for row in rows] == [8.5, 10.5]
    editor.restore(table_id, result.before)
    rows = store.list_records(table_id)
    assert [row["values"]["largura"] for row in rows] == [8.0, 10.0]


def test_batch_edit_is_atomic_when_one_value_is_invalid(tmp_path):
    store, table_id, first, second = make_table(tmp_path)
    editor = SpreadsheetBatchEditor(store)
    with pytest.raises(ValueError):
        editor.update_records(table_id, {
            first: {"largura": 9.0},
            second: {"nome": None},
        })
    rows = store.list_records(table_id)
    assert [row["values"]["largura"] for row in rows] == [8.0, 10.0]


def test_batch_edit_rejects_record_from_another_table(tmp_path):
    store, table_id, first, _ = make_table(tmp_path)
    other_table = store.create_table(store.list_projects()[0]["id"], "Outra")
    store.add_column(other_table, "nome", "text")
    other_record = store.insert_record(other_table, {"nome": "X"})
    with pytest.raises(BatchEditError):
        SpreadsheetBatchEditor(store).update_records(
            table_id, {first: {"largura": 9.0}, other_record: {"largura": 1.0}}
        )
