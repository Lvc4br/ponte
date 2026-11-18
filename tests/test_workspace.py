import csv

import pytest

from app.workspace.exchange import SpreadsheetExchange
from app.workspace.formulas import FormulaEngine, FormulaError
from app.workspace.store import WorkspaceStore


def build_store(tmp_path):
    store = WorkspaceStore(tmp_path / "workspace.sqlite3")
    project = store.create_project("Projeto genérico")
    return store, project


def test_projects_tables_columns_and_records_crud(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Medições")
    store.add_column(table, "Descrição", "text", required=True)
    store.add_column(table, "Quantidade", "decimal", default=0.0)
    record = store.insert_record(table, {"Descrição": "Concreto", "Quantidade": 12.5})
    assert store.list_records(table)[0]["values"] == {"Descrição": "Concreto", "Quantidade": 12.5}
    assert store.update_record(record, {"Quantidade": 15.0})
    assert store.list_records(table)[0]["values"]["Quantidade"] == 15.0
    assert store.delete_record(record)
    assert store.list_records(table) == []


def test_required_and_type_validation(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Dados")
    store.add_column(table, "Código", "integer", required=True)
    with pytest.raises(ValueError):
        store.insert_record(table, {})
    with pytest.raises(ValueError):
        store.insert_record(table, {"Código": "texto"})


def test_filters_sort_and_pagination(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Itens")
    store.add_column(table, "Nome")
    store.add_column(table, "Valor", "decimal")
    store.insert_record(table, {"Nome": "Aço", "Valor": 20})
    store.insert_record(table, {"Nome": "Concreto", "Valor": 10})
    result = store.list_records(table, filters={"Nome": {"contains": "con"}}, sort_by="Valor")
    assert [r["values"]["Nome"] for r in result] == ["Concreto"]
    assert store.list_records(table, sort_by="Valor", limit=1)[0]["values"]["Valor"] == 10


def test_delete_column_removes_values_without_touching_other_columns(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Itens")
    store.add_column(table, "Nome")
    value_column = store.add_column(table, "Preço", "decimal")
    store.insert_record(table, {"Nome": "Item", "Preço": 5})
    assert store.delete_column(value_column)
    assert store.list_records(table)[0]["values"] == {"Nome": "Item"}


def test_project_deletion_cascades_only_workspace_data(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Tabela")
    store.add_column(table, "Campo")
    store.insert_record(table, {"Campo": "Preservar até excluir projeto"})
    assert store.delete_project(project)
    assert store.list_projects() == []


def test_formula_engine_supports_math_and_functions():
    engine = FormulaEngine()
    assert engine.evaluate("=Quantidade * Preco", {"Quantidade": 3, "Preco": 2.5}) == 7.5
    assert engine.evaluate("SUM([1, 2, 3])") == 6
    assert engine.evaluate("IF(Valor > 10, ROUND(Valor / 3, 2), 0)", {"Valor": 12}) == 4


def test_formula_engine_rejects_code_execution():
    engine = FormulaEngine()
    with pytest.raises(FormulaError):
        engine.evaluate("__import__('os').system('echo unsafe')")
    with pytest.raises(FormulaError):
        engine.evaluate("open('arquivo')")
    with pytest.raises(FormulaError):
        engine.evaluate("Unknown + 1")


def test_csv_round_trip(tmp_path):
    store, project = build_store(tmp_path)
    source = tmp_path / "source.csv"
    source.write_text("Nome,Quantidade\nAço,3\nConcreto,5\n", encoding="utf-8")
    table = SpreadsheetExchange(store).import_csv(project, source)
    target = tmp_path / "export.csv"
    SpreadsheetExchange(store).export_csv(table, target)
    with target.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows == [["Nome", "Quantidade"], ["Aço", "3"], ["Concreto", "5"]]


def test_xlsx_imports_all_sheets_and_exports(tmp_path):
    from openpyxl import Workbook, load_workbook
    store, project = build_store(tmp_path)
    source = tmp_path / "source.xlsx"
    workbook = Workbook()
    workbook.active.title = "Resumo"
    workbook.active.append(["Item", "Valor"])
    workbook.active.append(["A", 10])
    detail = workbook.create_sheet("Detalhes")
    detail.append(["Código", "Ativo"])
    detail.append([1, True])
    workbook.save(source)
    exchange = SpreadsheetExchange(store)
    table_ids = exchange.import_xlsx(project, source)
    assert len(table_ids) == 2
    target = tmp_path / "export.xlsx"
    exchange.export_xlsx(table_ids[0], target)
    exported = load_workbook(target, data_only=True)
    assert exported.active["A2"].value == "A"


def test_rename_column_preserves_existing_values(tmp_path):
    store, project = build_store(tmp_path)
    table = store.create_table(project, "Itens")
    column = store.add_column(table, "Nome")
    store.insert_record(table, {"Nome": "Original"})
    assert store.rename_column(column, "Descrição")
    assert store.list_records(table)[0]["values"] == {"Descrição": "Original"}


def test_relationships_require_matching_column_types_and_same_project(tmp_path):
    store, project = build_store(tmp_path)
    first = store.create_table(project, "Projetos")
    second = store.create_table(project, "Tarefas")
    first_key = store.add_column(first, "Código", "integer")
    second_key = store.add_column(second, "Projeto", "integer")
    relation = store.create_relation(
        project, first, first_key, second, second_key, "one_to_many"
    )
    assert store.list_relations(project)[0]["id"] == relation
    text_key = store.add_column(second, "Texto", "text")
    with pytest.raises(ValueError):
        store.create_relation(project, first, first_key, second, text_key)


def test_workspace_additive_schema_preserves_legacy_records_table(tmp_path):
    import sqlite3
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
        db.execute("INSERT INTO records(payload) VALUES ('legacy payload')")
    store = WorkspaceStore(path)
    project = store.create_project("Novo")
    assert store.list_projects()[0]["id"] == project
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT payload FROM records").fetchone()[0] == "legacy payload"


def test_document_link_uses_existing_document_catalog(tmp_path):
    from app.documents.index import DocumentIndex
    from app.documents.scanner import DocumentScanner

    path = tmp_path / "shared.sqlite3"
    index = DocumentIndex(path)
    source = tmp_path / "memorial.txt"
    source.write_text("Memorial", encoding="utf-8")
    document_id = index.index_result(DocumentScanner().scan(source))
    store = WorkspaceStore(path)
    project = store.create_project("Obra")
    assert store.link_document(project, document_id)
    assert not store.link_document(project, document_id)
    assert store.list_project_documents(project)[0]["file_name"] == "memorial.txt"


def test_workspace_store_reopens_without_losing_tables_or_records(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    store = WorkspaceStore(path)
    project = store.create_project("Persistente")
    table = store.create_table(project, "Dados")
    store.add_column(table, "Valor", "integer")
    store.insert_record(table, {"Valor": 42})
    reopened = WorkspaceStore(path)
    assert reopened.list_records(table)[0]["values"]["Valor"] == 42
