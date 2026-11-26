from pathlib import Path

import pytest

from app.reports.exporter import export_report


@pytest.fixture
def sample_report_data():
    columns = [
        {"name": "OAE", "data_type": "text"},
        {"name": "Tipo", "data_type": "text"},
        {"name": "Comprimento", "data_type": "decimal"},
    ]
    records = [
        {"id": 1, "values": {"OAE": "OAE-001", "Tipo": "Ponte", "Comprimento": 120.5}},
        {"id": 2, "values": {"OAE": "OAE-002", "Tipo": "Viaduto", "Comprimento": 80.0}},
        {"id": 3, "values": {"OAE": "OAE-003", "Tipo": "Ponte", "Comprimento": 99.5}},
    ]
    return records, columns


@pytest.mark.parametrize("extension", ["xlsx", "docx", "pptx", "pdf"])
@pytest.mark.parametrize("chart_type", ["pie", "bar", "line", "radar"])
def test_export_report_formats_and_chart_types(tmp_path, sample_report_data, extension, chart_type):
    records, columns = sample_report_data
    target = tmp_path / f"report-{chart_type}.{extension}"

    result = export_report(
        records,
        columns,
        target,
        title="Relatório de teste",
        project_name="Projeto teste",
        table_name="OAEs",
        chart_type=chart_type,
        category_field="Tipo",
        value_field="Comprimento",
    )

    assert result == target
    assert target.is_file()
    assert target.stat().st_size > 500
    assert not (tmp_path / f".{target.stem}_chart.png").exists()

    if extension == "xlsx":
        from openpyxl import load_workbook
        workbook = load_workbook(target)
        assert "Relatório" in workbook.sheetnames
        assert "Dados" in workbook.sheetnames
        assert workbook["Dados"].max_row == 4
        assert len(workbook["Relatório"]._images) == 1
    elif extension == "docx":
        from docx import Document
        document = Document(target)
        assert any("Relatório de teste" in paragraph.text for paragraph in document.paragraphs)
        assert len(document.inline_shapes) == 1
    elif extension == "pptx":
        from pptx import Presentation
        presentation = Presentation(target)
        assert len(presentation.slides) >= 3
    else:
        assert target.read_bytes().startswith(b"%PDF")


def test_export_report_rejects_empty_records(tmp_path, sample_report_data):
    _records, columns = sample_report_data
    with pytest.raises(ValueError, match="Não há registros"):
        export_report([], columns, tmp_path / "empty.xlsx", value_field="Comprimento")


def test_export_report_rejects_unsupported_format(tmp_path, sample_report_data):
    records, columns = sample_report_data
    with pytest.raises(ValueError, match="Formato não suportado"):
        export_report(records, columns, tmp_path / "report.csv", value_field="Comprimento")


def test_export_report_rejects_non_numeric_chart_field(tmp_path):
    columns = [{"name": "Nome", "data_type": "text"}]
    records = [{"id": 1, "values": {"Nome": "Ponte"}}]
    with pytest.raises(ValueError, match="não contém valores numéricos"):
        export_report(
            records, columns, tmp_path / "report.pdf",
            category_field="Nome", value_field="Nome",
        )
