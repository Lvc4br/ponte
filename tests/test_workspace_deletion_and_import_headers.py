from app.workspace.exchange import SpreadsheetExchange
from app.workspace.store import WorkspaceStore


def test_import_drops_only_completely_empty_columns(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project_id = store.create_project("Projeto")
    headers = ["obra", "largura_m", None, None]
    rows = [[1, 12.4, None, None], [2, 10.5, None, None]]
    table_id = SpreadsheetExchange(store)._create_from_rows(
        project_id, "Base", headers, rows
    )
    columns = store.list_columns(table_id)
    records = store.list_records(table_id)
    assert [column["name"] for column in columns] == ["obra", "largura_m"]
    assert len(records) == 2


def test_import_keeps_unnamed_column_when_it_contains_data(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project_id = store.create_project("Projeto")
    table_id = SpreadsheetExchange(store)._create_from_rows(
        project_id, "Base", ["obra", None], [[1, "observação"]]
    )
    columns = store.list_columns(table_id)
    assert [column["name"] for column in columns] == ["obra", "Coluna 2"]
    assert store.list_records(table_id)[0]["values"]["Coluna 2"] == "observação"


def test_delete_table_removes_its_columns_and_records(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project_id = store.create_project("Projeto")
    table_id = store.create_table(project_id, "Base")
    store.add_column(table_id, "obra", "integer")
    store.insert_record(table_id, {"obra": 1})
    assert store.delete_table(table_id) is True
    assert store.list_tables(project_id) == []


def test_delete_project_removes_its_tables_and_records(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project_id = store.create_project("Projeto")
    table_id = store.create_table(project_id, "Base")
    store.add_column(table_id, "obra", "integer")
    store.insert_record(table_id, {"obra": 1})
    assert store.delete_project(project_id) is True
    assert store.list_projects() == []
    assert store.list_tables(project_id) == []
