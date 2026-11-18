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


def test_scans_pdf_pages(tmp_path):
    from pypdf import PdfWriter

    source = tmp_path / "manual.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with source.open("wb") as stream:
        writer.write(stream)

    result = DocumentScanner().scan(source)

    assert result.status == "partial"
    assert result.metadata["page_count"] == 1
    assert result.sections[0].locator == "page:1"


def test_scans_docx_paragraph_and_table(tmp_path):
    from docx import Document

    source = tmp_path / "memorial.docx"
    document = Document()
    document.add_paragraph("Memorial descritivo")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Quantidade"
    document.save(source)

    result = DocumentScanner().scan(source)

    assert result.status == "partial"
    assert any(section.kind == "paragraph" for section in result.sections)
    assert any(section.kind == "table" for section in result.sections)


def test_scans_xlsx_sheets_and_formula_expressions(tmp_path):
    from openpyxl import Workbook

    source = tmp_path / "quantitativos.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Quantitativos"
    sheet.append(["Item", "Quantidade"])
    sheet.append(["Concreto", 12])
    sheet["C2"] = "=B2*2"
    workbook.save(source)

    result = DocumentScanner().scan(source)

    assert result.status == "partial"
    assert result.metadata["sheet_names"] == ["Quantitativos"]
    rows = result.sections[0].content["rows"]
    assert rows[1][2] == "=B2*2"


def test_scans_pptx_slide_text(tmp_path):
    from pptx import Presentation
    from pptx.util import Inches

    source = tmp_path / "apresentacao.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    shape = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    shape.text = "Projeto executivo"
    presentation.save(source)

    result = DocumentScanner().scan(source)

    assert result.status == "partial"
    assert result.metadata["slide_count"] == 1
    assert "Projeto executivo" in str(result.sections[0].content)


def test_scans_dxf_entities_when_reader_is_installed(tmp_path):
    import ezdxf

    source = tmp_path / "desenho.dxf"
    drawing = ezdxf.new()
    drawing.modelspace().add_line((0, 0), (10, 5))
    drawing.saveas(source)

    result = DocumentScanner().scan(source)

    assert result.status == "success"
    assert result.metadata["entity_count"] == 1
    assert result.sections[0].kind == "cad_entities"


def test_scans_directory_recursively_in_batch(tmp_path):
    folder = tmp_path / "documentos"
    nested = folder / "subpasta"
    nested.mkdir(parents=True)
    (folder / "a.txt").write_text("A", encoding="utf-8")
    (nested / "b.csv").write_text("x,y\n1,2\n", encoding="utf-8")

    results = DocumentScanner().scan_many([folder])

    assert [result.file_name for result in results] == ["a.txt", "b.csv"]
    assert all(result.status == "success" for result in results)


def test_invalid_pdf_is_reported_as_error_without_stopping_batch(tmp_path):
    folder = tmp_path / "lote"
    folder.mkdir()
    (folder / "a.txt").write_text("válido", encoding="utf-8")
    (folder / "b.pdf").write_bytes(b"arquivo PDF inválido")

    results = DocumentScanner().scan_many([folder])

    assert len(results) == 2
    assert results[0].status == "success"
    assert results[1].status == "error"
    assert results[1].errors
