from app.documents.index import DocumentIndex
from app.documents.scanner import DocumentScanner


def test_document_index_persists_metadata_and_extracted_sections(tmp_path):
    source = tmp_path / "projeto.txt"
    source.write_text("Conteúdo técnico", encoding="utf-8")
    result = DocumentScanner().scan(source)
    index = DocumentIndex(tmp_path / "catalog.sqlite3")

    document_id = index.index_result(result)
    loaded = index.get_document(document_id)

    assert loaded["file_name"] == "projeto.txt"
    assert loaded["sha256"] == result.sha256
    assert loaded["sections"][0]["content"] == "Conteúdo técnico"
    assert len(index.list_documents()) == 1


def test_document_index_deduplicates_by_sha256(tmp_path):
    source = tmp_path / "original.txt"
    source.write_text("Mesmo conteúdo", encoding="utf-8")
    result = DocumentScanner().scan(source)
    index = DocumentIndex(tmp_path / "catalog.sqlite3")

    first_id = index.index_result(result)
    second_id = index.index_result(result)

    assert first_id == second_id
    assert len(index.list_documents()) == 1
    assert index.get_document(first_id)["sections"][0]["content"] == "Mesmo conteúdo"


def test_document_index_returns_none_for_unknown_id(tmp_path):
    index = DocumentIndex(tmp_path / "catalog.sqlite3")
    assert index.get_document(999) is None
