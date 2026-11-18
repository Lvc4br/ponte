"""Local-first document scanner with format-specific extractors.

The scanner extracts machine-accessible content; it does not certify or
semantically validate technical information.
"""

from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import shutil
import subprocess
import tempfile
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
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".rtf", ".odt", ".odp",
        ".xlsx", ".xlsm", ".xls", ".xlsb", ".csv", ".txt", ".md", ".json",
        ".xml", ".dxf", ".dwg", ".ifc", ".png", ".jpg", ".jpeg", ".tif",
        ".tiff", ".bmp", ".webp", ".gif",
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
        results = []
        for item in unique:
            try:
                results.append(self.scan(item))
            except Exception as exc:
                results.append(DocumentScanResult(
                    path=str(item), file_name=item.name, extension=item.suffix.lower(),
                    mime_type=mimetypes.guess_type(item.name)[0], size_bytes=0,
                    sha256="", status="error",
                    errors=[f"{type(exc).__name__}: {exc}"],
                ))
        return results

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
                ".doc": self._office_text,
                ".docx": self._docx,
                ".ppt": self._office_text,
                ".pptx": self._pptx,
                ".rtf": self._office_text,
                ".odt": self._office_text,
                ".odp": self._office_text,
                ".xlsx": self._excel,
                ".xlsm": self._excel,
                ".xls": self._xls,
                ".xlsb": self._xlsb,
                ".csv": self._csv,
                ".txt": self._text,
                ".md": self._text,
                ".json": self._text,
                ".xml": self._text,
                ".dxf": self._dxf,
                ".dwg": self._dwg,
                ".ifc": self._ifc,
                ".png": self._image,
                ".jpg": self._image,
                ".jpeg": self._image,
                ".tif": self._image,
                ".tiff": self._image,
                ".bmp": self._image,
                ".webp": self._image,
                ".gif": self._image,
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
            "form_fields": reader.get_fields() or {},
            "attachments": sorted((reader.attachments or {}).keys()),
        })
        if reader.is_encrypted:
            result.warnings.append("PDF protegido por senha; conteúdo não extraído.")
            return
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            result.sections.append(ExtractedSection("page_text", f"page:{index}", text))
            if not text.strip():
                ocr_text, warning = DocumentScanner._ocr_pdf_page(path, index - 1)
                if ocr_text:
                    result.sections.append(ExtractedSection(
                        "ocr_text", f"page:{index}:ocr", ocr_text
                    ))
                if warning:
                    result.warnings.append(f"Página {index}: {warning}")
                elif not ocr_text:
                    result.warnings.append(f"Página {index} sem texto reconhecido por OCR.")
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    for table_number, table in enumerate(page.extract_tables() or [], start=1):
                        result.sections.append(ExtractedSection(
                            "pdf_table", f"page:{page_number}:table:{table_number}", table
                        ))
        except ImportError:
            result.warnings.append("Extração de tabelas PDF indisponível; instale pdfplumber.")
        except Exception as exc:
            result.warnings.append(f"Extração de tabelas PDF incompleta: {exc}")

    @staticmethod
    def _ocr_pdf_page(path: Path, page_index: int) -> tuple[str, str | None]:
        try:
            import pypdfium2 as pdfium
            import pytesseract
        except ImportError:
            return "", "OCR indisponível; instale pypdfium2, Pillow, pytesseract e Tesseract."
        document = None
        try:
            document = pdfium.PdfDocument(str(path))
            page = document[page_index]
            image = page.render(scale=2).to_pil()
            try:
                text = pytesseract.image_to_string(image, lang="por+eng")
            except Exception:
                text = pytesseract.image_to_string(image, lang="eng")
            return text, None
        except Exception as exc:
            return "", f"falha no OCR ({exc})."
        finally:
            if document is not None:
                document.close()

    @staticmethod
    def _office_text(path: Path, result: DocumentScanResult) -> None:
        """Extract legacy binary DOC through a locally installed LibreOffice."""
        executable = shutil.which("soffice") or shutil.which("libreoffice")
        if not executable:
            result.warnings.append(
                f"{path.suffix.upper()} detectado, mas a leitura exige LibreOffice instalado "
                "ou conversão prévia para um formato suportado."
            )
            return
        with tempfile.TemporaryDirectory(prefix="ponte_doc_") as temporary:
            output_dir = Path(temporary)
            completed = subprocess.run(
                [
                    executable, "--headless", "--convert-to", "txt:Text",
                    "--outdir", str(output_dir), str(path),
                ],
                capture_output=True, text=True, timeout=120, check=False,
            )
            output = output_dir / f"{path.stem}.txt"
            if completed.returncode != 0 or not output.is_file():
                detail = (completed.stderr or completed.stdout or "conversão não concluída").strip()
                result.warnings.append(f"Não foi possível converter o DOC: {detail[:500]}")
                return
            content = output.read_text(encoding="utf-8", errors="replace")
            result.metadata["converted_with"] = Path(executable).name
            result.sections.append(ExtractedSection("text", "document:1", content))
            result.warnings.append(
                f"{path.suffix.upper()} convertido localmente para texto; estrutura visual, "
                "tabelas complexas, notas e objetos incorporados podem não ser preservados."
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
    def _xlsb(path: Path, result: DocumentScanResult) -> None:
        try:
            from pyxlsb import open_workbook
        except ImportError:
            result.warnings.append("Leitor XLSB ausente; instale pyxlsb para habilitar o formato.")
            return
        with open_workbook(str(path)) as workbook:
            result.metadata.update({
                "sheet_names": list(workbook.sheets),
                "sheet_count": len(workbook.sheets),
            })
            for sheet_name in workbook.sheets:
                with workbook.get_sheet(sheet_name) as sheet:
                    rows = [[cell.v for cell in row] for row in sheet.rows()]
                result.sections.append(ExtractedSection(
                    "worksheet", f"sheet:{sheet_name}",
                    {"title": sheet_name, "rows": rows},
                ))
        result.warnings.append("XLSB: fórmulas, macros e objetos incorporados não são executados.")

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
            try:
                try:
                    text = pytesseract.image_to_string(image, lang="por+eng")
                except Exception:
                    text = pytesseract.image_to_string(image, lang="eng")
                result.sections.append(ExtractedSection("ocr_text", "image:1", text))
            except Exception as exc:
                result.warnings.append(
                    f"OCR indisponível nesta máquina; verifique o Tesseract: {exc}"
                )

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
    def _dwg(path: Path, result: DocumentScanResult) -> None:
        """Convert DWG to DXF using an optional ODA File Converter installation."""
        executable = shutil.which("ODAFileConverter") or shutil.which("ODAFileConverter.exe")
        if not executable:
            result.warnings.append(
                "DWG detectado, mas exige ODA File Converter instalado. "
                "Também é possível exportar o desenho para DXF."
            )
            return
        with tempfile.TemporaryDirectory(prefix="ponte_dwg_") as temporary:
            root = Path(temporary)
            source_dir, target_dir = root / "source", root / "target"
            source_dir.mkdir()
            target_dir.mkdir()
            shutil.copy2(path, source_dir / path.name)
            completed = subprocess.run(
                [executable, str(source_dir), str(target_dir), "ACAD2018", "DXF", "0", "1"],
                capture_output=True, text=True, timeout=300, check=False,
            )
            converted = target_dir / f"{path.stem}.dxf"
            if completed.returncode != 0 or not converted.is_file():
                detail = (completed.stderr or completed.stdout or "conversão não concluída").strip()
                result.warnings.append(f"Falha na conversão DWG: {detail[:500]}")
                return
            result.metadata["converted_with"] = Path(executable).name
            DocumentScanner._dxf(converted, result)
            result.warnings.append(
                "DWG convertido para DXF por ferramenta externa; confirme fidelidade de entidades e cotas."
            )

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
