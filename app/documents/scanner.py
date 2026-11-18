"""Local-first document scanner with format-specific extractors.

The scanner extracts machine-accessible content; it does not certify or
semantically validate technical information.
"""

from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExtractedSection:
    kind: str
    locator: str
    content: Any


@dataclass
class DocumentScanResult:
    path: str
    file_name: str
    extension: str
    mime_type: str | None
    size_bytes: int
    sha256: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: list[ExtractedSection] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "sections": [asdict(section) for section in self.sections],
        }


class DocumentScanner:
    """Inspect supported office, text, PDF, image and technical file formats."""

    MAX_FILE_SIZE = 512 * 1024 * 1024
    SUPPORTED = {
        ".pdf", ".docx", ".xlsx", ".xlsm", ".xls", ".pptx",
        ".csv", ".txt", ".md", ".json", ".xml", ".dxf",
        ".ifc", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp",
    }

    def scan_many(self, paths: list[str | Path]) -> list[DocumentScanResult]:
        """Scan files and directory contents; isolate errors per file."""
        candidates: list[Path] = []
        for item in paths:
            path = Path(item).expanduser()
            if path.is_dir():
                candidates.extend(child for child in path.rglob("*") if child.is_file())
            elif path.is_file():
                candidates.append(path)
        unique = sorted({item.resolve() for item in candidates}, key=lambda item: str(item).casefold())
        return [self.scan(item) for item in unique]

    def scan(self, file_path: str | Path) -> DocumentScanResult:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        stat = path.stat()
        if stat.st_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"Arquivo excede o limite de {self.MAX_FILE_SIZE // (1024 * 1024)} MB."
            )
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)

        extension = path.suffix.lower()
        result = DocumentScanResult(
            path=str(path), file_name=path.name, extension=extension,
            mime_type=mimetypes.guess_type(path.name)[0],
            size_bytes=stat.st_size, sha256=digest.hexdigest(),
            status="unsupported" if extension not in self.SUPPORTED else "scanned",
            metadata={"modified_timestamp": stat.st_mtime},
        )
        if result.status == "unsupported":
            result.warnings.append(
                f"Formato {extension or '(sem extensão)'} ainda não possui leitor integrado."
            )
            return result

        try:
            handler = {
                ".pdf": self._pdf,
                ".docx": self._docx,
                ".xlsx": self._excel,
                ".xlsm": self._excel,
                ".xls": self._xls,
                ".pptx": self._pptx,
                ".csv": self._csv,
                ".txt": self._text,
                ".md": self._text,
                ".json": self._text,
                ".xml": self._text,
                ".dxf": self._dxf,
                ".ifc": self._ifc,
                ".png": self._image,
                ".jpg": self._image,
                ".jpeg": self._image,
                ".tif": self._image,
                ".tiff": self._image,
                ".bmp": self._image,
            }[extension]
            handler(path, result)
            if result.errors:
                result.status = "partial"
            elif result.warnings:
                result.status = "partial"
            else:
                result.status = "success"
        except Exception as exc:  # Keep batch scanning resilient to one bad file.
            result.status = "error"
            result.errors.append(f"{type(exc).__name__}: {exc}")
        return result

    @staticmethod
    def _pdf(path: Path, result: DocumentScanResult) -> None:
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=False)
        result.metadata.update({
            "page_count": len(reader.pages),
            "document_info": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
            "encrypted": bool(reader.is_encrypted),
        })
        if reader.is_encrypted:
            result.warnings.append("PDF protegido por senha; conteúdo não extraído.")
            return
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            result.sections.append(ExtractedSection("page_text", f"page:{index}", text))
            if not text.strip():
                result.warnings.append(
                    f"Página {index} sem texto extraível; pode exigir OCR."
                )

    @staticmethod
    def _docx(path: Path, result: DocumentScanResult) -> None:
        from docx import Document

        document = Document(str(path))
        result.metadata["paragraph_count"] = len(document.paragraphs)
        result.metadata["table_count"] = len(document.tables)
        for index, paragraph in enumerate(document.paragraphs, start=1):
            if paragraph.text.strip():
                result.sections.append(ExtractedSection(
                    "paragraph", f"paragraph:{index}", paragraph.text
                ))
        for table_index, table in enumerate(document.tables, start=1):
            rows = [[cell.text for cell in row.cells] for row in table.rows]
            result.sections.append(ExtractedSection(
                "table", f"table:{table_index}", rows
            ))
        for section_index, section in enumerate(document.sections, start=1):
            for label, part in (("header", section.header), ("footer", section.footer)):
                text = "\n".join(p.text for p in part.paragraphs if p.text.strip())
                if text:
                    result.sections.append(ExtractedSection(
                        label, f"section:{section_index}:{label}", text
                    ))
        result.warnings.append(
            "Caixas de texto, comentários, alterações controladas e objetos incorporados podem exigir leitores adicionais."
        )

    @staticmethod
    def _excel(path: Path, result: DocumentScanResult) -> None:
        from openpyxl import load_workbook

        workbook = load_workbook(path, read_only=True, data_only=False)
        result.metadata.update({
            "sheet_names": workbook.sheetnames,
            "sheet_count": len(workbook.sheetnames),
            "calculation_mode": str(getattr(workbook.calculation, "calcMode", "")),
        })
        for sheet in workbook.worksheets:
            rows = []
            for row in sheet.iter_rows(values_only=True):
                rows.append(list(row))
            result.sections.append(ExtractedSection(
                "worksheet", f"sheet:{sheet.title}",
                {"title": sheet.title, "max_row": sheet.max_row,
                 "max_column": sheet.max_column, "rows": rows},
            ))
        workbook.close()
        result.warnings.append(
            "Fórmulas são preservadas como expressões; macros VBA e objetos incorporados não são executados nem interpretados."
        )

    @staticmethod
    def _xls(path: Path, result: DocumentScanResult) -> None:
        import xlrd

        workbook = xlrd.open_workbook(str(path), on_demand=True)
        result.metadata.update({
            "sheet_names": workbook.sheet_names(),
            "sheet_count": workbook.nsheets,
        })
        for sheet in workbook.sheets():
            rows = [sheet.row_values(index) for index in range(sheet.nrows)]
            result.sections.append(ExtractedSection(
                "worksheet", f"sheet:{sheet.name}",
                {"title": sheet.name, "max_row": sheet.nrows,
                 "max_column": sheet.ncols, "rows": rows},
            ))
        workbook.release_resources()
        result.warnings.append("O formato XLS legado não expõe fórmulas com a mesma fidelidade do XLSX.")

    @staticmethod
    def _pptx(path: Path, result: DocumentScanResult) -> None:
        from pptx import Presentation

        presentation = Presentation(str(path))
        result.metadata["slide_count"] = len(presentation.slides)
        for slide_number, slide in enumerate(presentation.slides, start=1):
            items = []
            for shape in slide.shapes:
                if getattr(shape, "has_text_frame", False) and shape.text.strip():
                    items.append({"type": "text", "text": shape.text})
                if getattr(shape, "has_table", False):
                    items.append({
                        "type": "table",
                        "rows": [[cell.text for cell in row.cells] for row in shape.table.rows],
                    })
            result.sections.append(ExtractedSection(
                "slide", f"slide:{slide_number}", items
            ))
        result.warnings.append("Imagens, gráficos e objetos incorporados não são convertidos em dados sem leitores adicionais.")

    @staticmethod
    def _csv(path: Path, result: DocumentScanResult) -> None:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            sample = stream.read(8192)
            stream.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel
            rows = list(csv.reader(stream, dialect))
        result.metadata.update({"row_count": len(rows), "column_count": max(map(len, rows), default=0)})
        result.sections.append(ExtractedSection("table", "csv:1", rows))

    @staticmethod
    def _text(path: Path, result: DocumentScanResult) -> None:
        raw = path.read_bytes()
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("cp1252")
            result.warnings.append("Codificação CP1252 usada como alternativa ao UTF-8.")
        result.metadata["character_count"] = len(content)
        result.sections.append(ExtractedSection("text", "document:1", content))
        if path.suffix.lower() == ".json":
            try:
                result.sections.append(ExtractedSection(
                    "structured_data", "json:1", json.loads(content)
                ))
            except json.JSONDecodeError as exc:
                result.warnings.append(f"JSON não validado: {exc}")

    @staticmethod
    def _image(path: Path, result: DocumentScanResult) -> None:
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:
            result.warnings.append(
                "OCR indisponível: instale Pillow e pytesseract e configure o Tesseract OCR."
            )
            result.metadata["ocr_dependency_error"] = str(exc)
            return
        with Image.open(path) as image:
            result.metadata.update({
                "image_width": image.width, "image_height": image.height,
                "image_mode": image.mode,
            })
            result.sections.append(ExtractedSection(
                "ocr_text", "image:1", pytesseract.image_to_string(image)
            ))

    @staticmethod
    def _dxf(path: Path, result: DocumentScanResult) -> None:
        try:
            import ezdxf
        except ImportError:
            result.warnings.append("Leitor DXF opcional ausente; instale ezdxf para habilitá-lo.")
            return
        drawing = ezdxf.readfile(path)
        modelspace = drawing.modelspace()
        entities = []
        for entity in modelspace:
            item = {"type": entity.dxftype(), "layer": entity.dxf.get("layer")}
            for attribute in ("text", "insert", "start", "end", "center", "radius"):
                if entity.dxf.hasattr(attribute):
                    item[attribute] = str(entity.dxf.get(attribute))
            entities.append(item)
        result.metadata.update({
            "dxf_version": drawing.dxfversion,
            "layer_names": [layer.dxf.name for layer in drawing.layers],
            "entity_count": len(entities),
        })
        result.sections.append(ExtractedSection("cad_entities", "modelspace", entities))

    @staticmethod
    def _ifc(path: Path, result: DocumentScanResult) -> None:
        try:
            import ifcopenshell
        except ImportError:
            result.warnings.append(
                "Leitor IFC opcional ausente; instale IfcOpenShell compatível com seu Python."
            )
            return
        model = ifcopenshell.open(str(path))
        entities = []
        for element in model.by_type("IfcProduct"):
            entities.append({
                "global_id": getattr(element, "GlobalId", None),
                "ifc_type": element.is_a(),
                "name": getattr(element, "Name", None),
                "description": getattr(element, "Description", None),
            })
        result.metadata["ifc_schema"] = model.schema
        result.metadata["product_count"] = len(entities)
        result.sections.append(ExtractedSection("bim_products", "ifc:products", entities))
