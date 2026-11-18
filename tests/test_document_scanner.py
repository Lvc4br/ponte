from app.documents.scanner import DocumentScanner


def test_scans_utf8_text_and_calculates_fingerprint(tmp_path):
    source = tmp_path / "relatorio.txt"
    source.write_text("Relatório técnico\nEstrutura: ponte", encoding="utf-8")
    result = DocumentScanner().scan(source)
    assert result.status == "success"
    assert result.extension == ".txt"
    assert len(result.sha256) == 64
    assert result.sections[0].kind == "text"
    assert "Relatório técnico" in result.sections[0].content


def test_scans_csv_as_rows(tmp_path):
    source = tmp_path / "dados.csv"
    source.write_text("nome;valor\nA;10\nB;20\n", encoding="utf-8")
    result = DocumentScanner().scan(source)
    assert result.status == "success"
    assert result.metadata["row_count"] == 3
    assert result.sections[0].content[1] == ["A", "10"]


def test_scans_json_and_exposes_structured_data(tmp_path):
    source = tmp_path / "dados.json"
    source.write_text('{"projeto": "A", "quantidade": 3}', encoding="utf-8")
    result = DocumentScanner().scan(source)
    assert result.status == "success"
    assert result.sections[1].kind == "structured_data"
    assert result.sections[1].content["quantidade"] == 3


def test_unsupported_format_is_reported_without_crashing(tmp_path):
    source = tmp_path / "modelo.rvt"
    source.write_bytes(b"placeholder")
    result = DocumentScanner().scan(source)
    assert result.status == "unsupported"
    assert result.sections == []
    assert result.warnings


def test_missing_file_raises_clear_error(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        DocumentScanner().scan(tmp_path / "nao-existe.pdf")
