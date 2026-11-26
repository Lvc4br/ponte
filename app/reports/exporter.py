"""Export filtered workspace records to editable office documents and PDF."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import math
from pathlib import Path
from typing import Iterable


SUPPORTED_FORMATS = {"xlsx", "docx", "pptx", "pdf"}
SUPPORTED_CHARTS = {"pie", "bar", "line", "radar"}


def _chart_image(records, chart_type, category_field, value_field, destination):
    if chart_type not in SUPPORTED_CHARTS:
        raise ValueError(f"Tipo de gráfico não suportado: {chart_type}")
    if not value_field:
        raise ValueError("Selecione um campo numérico para o gráfico.")

    grouped = defaultdict(float)
    for index, record in enumerate(records, start=1):
        values = record.get("values", {})
        raw = values.get(value_field)
        try:
            if raw is None or isinstance(raw, bool):
                continue
            if isinstance(raw, str):
                raw = raw.strip().replace(" ", "")
                if "," in raw and "." in raw:
                    raw = raw.replace(".", "").replace(",", ".")
                else:
                    raw = raw.replace(",", ".")
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(number):
            continue
        category = str(values.get(category_field) or f"Registro {index}") if category_field else f"Registro {index}"
        grouped[category] += number

    if not grouped:
        raise ValueError(f"O campo '{value_field}' não contém valores numéricos válidos.")
    labels = list(grouped)
    values = [grouped[label] for label in labels]
    if chart_type == "pie" and (any(value < 0 for value in values) or sum(values) <= 0):
        raise ValueError("O gráfico de pizza exige valores não negativos e soma maior que zero.")

    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    figure = Figure(figsize=(9, 4.8), dpi=150, tight_layout=True)
    FigureCanvasAgg(figure)
    if chart_type == "pie":
        axes = figure.add_subplot(111)
        axes.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, wedgeprops={"width": 0.45})
        axes.axis("equal")
    elif chart_type == "bar":
        axes = figure.add_subplot(111)
        axes.bar(labels, values)
        axes.set_ylabel(value_field)
        axes.tick_params(axis="x", labelrotation=35)
    elif chart_type == "line":
        axes = figure.add_subplot(111)
        axes.plot(labels, values, marker="o")
        axes.set_ylabel(value_field)
        axes.tick_params(axis="x", labelrotation=35)
        axes.grid(True, alpha=0.25)
    else:
        axes = figure.add_subplot(111, polar=True)
        angles = [index / float(len(labels)) * 6.283185307179586 for index in range(len(labels))]
        angles += angles[:1]
        radar_values = values + values[:1]
        axes.plot(angles, radar_values, linewidth=2)
        axes.fill(angles, radar_values, alpha=0.2)
        axes.set_xticks(angles[:-1])
        axes.set_xticklabels(labels)
    figure.savefig(destination, format="png", bbox_inches="tight")
    figure.clear()
    return Path(destination)


def export_report(
    records: Iterable[dict],
    columns: Iterable[dict],
    destination: str | Path,
    *,
    title: str = "Relatório de dados",
    project_name: str = "",
    table_name: str = "",
    chart_type: str = "bar",
    category_field: str = "",
    value_field: str = "",
    filters_note: str = "Registros conforme o recorte exibido na análise.",
) -> Path:
    """Create XLSX, DOCX, PPTX or PDF using only the supplied filtered records."""
    records = list(records)
    columns = list(columns)
    target = Path(destination)
    extension = target.suffix.lower().lstrip(".")
    if extension not in SUPPORTED_FORMATS:
        raise ValueError("Formato não suportado. Use XLSX, DOCX, PPTX ou PDF.")
    if not records:
        raise ValueError("Não há registros no recorte atual para exportar.")
    if not columns:
        raise ValueError("O conjunto selecionado não possui colunas para exportação.")
    target.parent.mkdir(parents=True, exist_ok=True)

    chart_path = target.with_name(f".{target.stem}_chart.png")
    _chart_image(records, chart_type, category_field, value_field, chart_path)
    headers = [column["name"] for column in columns]
    rows = [[record.get("values", {}).get(name) for name in headers] for record in records]
    generated = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z")
    metadata = [
        ("Projeto", project_name or "Não informado"),
        ("Conjunto", table_name or "Não informado"),
        ("Registros", str(len(records))),
        ("Gerado em", generated),
        ("Recorte", filters_note),
        ("Gráfico", f"{chart_type} · {category_field} × {value_field}"),
    ]

    try:
        if extension == "xlsx":
            _export_xlsx(target, headers, rows, metadata, chart_path)
        elif extension == "docx":
            _export_docx(target, title, headers, rows, metadata, chart_path)
        elif extension == "pptx":
            _export_pptx(target, title, headers, rows, metadata, chart_path)
        else:
            _export_pdf(target, title, headers, rows, metadata, chart_path)
    finally:
        chart_path.unlink(missing_ok=True)
    return target


def _export_xlsx(target, headers, rows, metadata, chart_path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.drawing.image import Image

    workbook = Workbook()
    summary = workbook.active
    summary.title = "Relatório"
    summary.append(["PONTE · RELATÓRIO"])
    summary["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    summary["A1"].fill = PatternFill("solid", fgColor="173F5F")
    summary.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
    for label, value in metadata:
        summary.append([label, value])
    summary.column_dimensions["A"].width = 22
    summary.column_dimensions["B"].width = 64
    for row in summary.iter_rows(min_row=2, max_col=2):
        row[0].font = Font(bold=True, color="294B67")
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
    image = Image(str(chart_path))
    image.width, image.height = 720, 385
    summary.add_image(image, "A10")

    data = workbook.create_sheet("Dados")
    data.append(headers)
    for row in rows:
        data.append([_excel_value(value) for value in row])
    data.freeze_panes = "A2"
    data.auto_filter.ref = data.dimensions
    for cell in data[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="287DB5")
    for index, header in enumerate(headers, start=1):
        data.column_dimensions[data.cell(1, index).column_letter].width = min(max(len(header) + 3, 14), 36)
    workbook.save(target)


def _excel_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _export_docx(target, title, headers, rows, metadata, chart_path):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor

    document = Document()
    heading = document.add_heading(title, 0)
    heading.runs[0].font.color.rgb = RGBColor(23, 63, 95)
    document.add_paragraph("PONTE · Relatório gerado a partir do recorte selecionado")
    table = document.add_table(rows=0, cols=2)
    table.style = "Light Shading Accent 1"
    for label, value in metadata:
        cells = table.add_row().cells
        cells[0].text = label
        cells[1].text = value
    document.add_heading("Visualização gráfica", level=1)
    document.add_picture(str(chart_path), width=Inches(6.2))
    document.add_heading("Dados exportados", level=1)
    data_table = document.add_table(rows=1, cols=len(headers))
    data_table.style = "Table Grid"
    for cell, header in zip(data_table.rows[0].cells, headers):
        cell.text = str(header)
    for row in rows:
        cells = data_table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = "" if value is None else str(value)
    document.save(target)


def _export_pptx(target, title, headers, rows, metadata, chart_path):
    from pptx import Presentation
    from pptx.util import Inches, Pt

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = "PONTE · Relatório gerado a partir do recorte selecionado"
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = "Resumo e gráfico"
    textbox = slide.shapes.add_textbox(Inches(0.55), Inches(1.05), Inches(3.6), Inches(2.0))
    frame = textbox.text_frame
    frame.clear()
    for label, value in metadata:
        paragraph = frame.add_paragraph()
        paragraph.text = f"{label}: {value}"
        paragraph.font.size = Pt(12)
    slide.shapes.add_picture(str(chart_path), Inches(4.1), Inches(1.15), width=Inches(8.4))
    chunk_size = 16
    for start in range(0, len(rows), chunk_size):
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = f"Dados exportados · {start + 1}–{min(start + chunk_size, len(rows))}"
        table = slide.shapes.add_table(
            min(chunk_size, len(rows) - start) + 1, len(headers),
            Inches(0.35), Inches(1.2), Inches(12.6), Inches(5.7)
        ).table
        for column, header in enumerate(headers):
            table.cell(0, column).text = str(header)
        for row_index, row in enumerate(rows[start:start + chunk_size], start=1):
            for column, value in enumerate(row):
                table.cell(row_index, column).text = "" if value is None else str(value)
    presentation.save(target)


def _export_pdf(target, title, headers, rows, metadata, chart_path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    document = SimpleDocTemplate(
        str(target), pagesize=landscape(A4),
        rightMargin=12 * mm, leftMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 5 * mm)]
    story.append(Paragraph("PONTE · Relatório gerado a partir do recorte selecionado", styles["Normal"]))
    story.append(Spacer(1, 3 * mm))
    meta = Table([["Campo", "Informação"]] + [list(item) for item in metadata], colWidths=[42 * mm, 210 * mm])
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173F5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5DF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([meta, Spacer(1, 5 * mm), Paragraph("Visualização gráfica", styles["Heading2"])])
    story.append(Image(str(chart_path), width=245 * mm, height=130 * mm))
    story.extend([Spacer(1, 4 * mm), Paragraph("Dados exportados", styles["Heading2"])])
    safe_headers = [Paragraph(str(header), styles["BodyText"]) for header in headers]
    safe_rows = [[Paragraph("" if value is None else str(value), styles["BodyText"]) for value in row] for row in rows]
    available_width = landscape(A4)[0] - 24 * mm
    column_width = available_width / max(1, len(headers))
    data = Table([safe_headers] + safe_rows, colWidths=[column_width] * len(headers), repeatRows=1)
    data.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#287DB5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7E0E8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(data)
    document.build(story)
