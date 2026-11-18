"""Import/export adapters for generic workspace tables (CSV and Excel)."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from app.workspace.store import WorkspaceStore


class SpreadsheetExchange:
    def __init__(self, store: WorkspaceStore):
        self.store = store

    @staticmethod
    def _infer_type(values):
        present = [value for value in values if value is not None and value != ""]
        if not present:
            return "text"
        if all(isinstance(v, bool) for v in present):
            return "boolean"
        if all(isinstance(v, datetime) for v in present):
            return "datetime"
        if all(isinstance(v, date) and not isinstance(v, datetime) for v in present):
            return "date"
        if all(isinstance(v, int) and not isinstance(v, bool) for v in present):
            return "integer"
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in present):
            return "decimal"
        return "text"

    @staticmethod
    def _unique_headers(headers):
        result, counts = [], {}
        for index, header in enumerate(headers, start=1):
            name = str(header).strip() or f"Coluna {index}"
            counts[name] = counts.get(name, 0) + 1
            result.append(name if counts[name] == 1 else f"{name} ({counts[name]})")
        return result

    def _assert_table_name_available(self, project_id, name):
        existing = {
            table["name"].casefold() for table in self.store.list_tables(project_id)
        }
        if str(name).strip().casefold() in existing:
            raise ValueError(
                f"Já existe uma tabela chamada '{name}' neste projeto. "
                "Renomeie a tabela existente ou escolha outro nome para a importação."
            )

    def _create_from_rows(self, project_id, name, headers, rows, description=""):
        headers = self._unique_headers(headers)
        self._assert_table_name_available(project_id, name)
        table_id = self.store.create_table(project_id, name, description)
        try:
            inferred = []
            for index, header in enumerate(headers):
                values = [row[index] if index < len(row) else None for row in rows]
                data_type = self._infer_type(values)
                inferred.append(data_type)
                self.store.add_column(table_id, header, data_type, position=index)
            for row in rows:
                values = {}
                for index, header in enumerate(headers):
                    value = row[index] if index < len(row) else None
                    if isinstance(value, (datetime, date)):
                        value = value.isoformat()
                    elif value is not None and inferred[index] == "text" and not isinstance(value, str):
                        value = str(value)
                    values[header] = value
                self.store.insert_record(table_id, values)
            return table_id
        except Exception:
            self.store.delete_table(table_id)
            raise

    def preview_csv(self, path: str | Path, *, limit=10, encoding="utf-8-sig", delimiter=None):
        path = Path(path)
        with path.open("r", encoding=encoding, newline="") as stream:
            sample = stream.read(8192)
            stream.seek(0)
            if delimiter is None:
                try:
                    delimiter = csv.Sniffer().sniff(sample).delimiter
                except csv.Error:
                    delimiter = ","
            reader = csv.reader(stream, delimiter=delimiter)
            rows = []
            for index, row in enumerate(reader):
                if index > max(0, int(limit)):
                    break
                rows.append(row)
        return {"file_name": path.name, "rows": rows, "delimiter": delimiter}

    def preview_xlsx(self, path: str | Path, *, limit=10):
        from openpyxl import load_workbook

        path = Path(path)
        workbook = load_workbook(path, read_only=True, data_only=False)
        try:
            previews = []
            for sheet in workbook.worksheets:
                rows = [
                    list(row) for row in sheet.iter_rows(
                        max_row=max(1, int(limit) + 1), values_only=True
                    )
                ]
                previews.append({"sheet_name": sheet.title, "rows": rows})
            return {"file_name": path.name, "sheets": previews}
        finally:
            workbook.close()

    def import_csv(self, project_id: int, path: str | Path, *, table_name=None,
                   encoding="utf-8-sig", delimiter=None):
        path = Path(path)
        with path.open("r", encoding=encoding, newline="") as stream:
            sample = stream.read(8192)
            stream.seek(0)
            if delimiter is None:
                try:
                    delimiter = csv.Sniffer().sniff(sample).delimiter
                except csv.Error:
                    delimiter = ","
            rows = list(csv.reader(stream, delimiter=delimiter))
        if not rows:
            raise ValueError("O CSV está vazio.")
        return self._create_from_rows(
            project_id, table_name or path.stem, rows[0], rows[1:],
            f"Importado de {path.name}",
        )

    def import_xlsx(self, project_id: int, path: str | Path, *, sheet_name=None):
        from openpyxl import load_workbook

        path = Path(path)
        workbook = load_workbook(path, read_only=True, data_only=False)
        try:
            if sheet_name is not None and sheet_name not in workbook.sheetnames:
                raise KeyError(f"Aba não encontrada: {sheet_name}")
            sheets = [workbook[sheet_name]] if sheet_name else list(workbook.worksheets)
            created = []
            try:
                for sheet in sheets:
                    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
                    while rows and not any(value is not None for value in rows[-1]):
                        rows.pop()
                    if not rows:
                        continue
                    created.append(self._create_from_rows(
                        project_id, sheet.title, rows[0], rows[1:],
                        f"Importado de {path.name}, aba {sheet.title}",
                    ))
                return created
            except Exception:
                for table_id in created:
                    self.store.delete_table(table_id)
                raise
        finally:
            workbook.close()

    def import_xls(self, project_id: int, path: str | Path, *, sheet_name=None):
        import xlrd

        path = Path(path)
        workbook = xlrd.open_workbook(str(path), on_demand=True)
        created = []
        try:
            names = workbook.sheet_names()
            if sheet_name is not None and sheet_name not in names:
                raise KeyError(f"Aba não encontrada: {sheet_name}")
            selected = [sheet_name] if sheet_name else names
            try:
                for name in selected:
                    sheet = workbook.sheet_by_name(name)
                    rows = []
                    for row_index in range(sheet.nrows):
                        row = []
                        for cell in sheet.row(row_index):
                            if cell.ctype == xlrd.XL_CELL_DATE:
                                row.append(xlrd.xldate_as_datetime(cell.value, workbook.datemode).isoformat())
                            elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                                row.append(bool(cell.value))
                            elif cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                                row.append(None)
                            else:
                                row.append(cell.value)
                        rows.append(row)
                    if rows:
                        created.append(self._create_from_rows(
                            project_id, name, rows[0], rows[1:],
                            f"Importado de {path.name}, aba {name}",
                        ))
                return created
            except Exception:
                for table_id in created:
                    self.store.delete_table(table_id)
                raise
        finally:
            workbook.release_resources()

    def import_xlsb(self, project_id: int, path: str | Path, *, sheet_name=None):
        from pyxlsb import open_workbook

        path = Path(path)
        created = []
        with open_workbook(str(path)) as workbook:
            if sheet_name is not None and sheet_name not in workbook.sheets:
                raise KeyError(f"Aba não encontrada: {sheet_name}")
            selected = [sheet_name] if sheet_name else list(workbook.sheets)
            try:
                for name in selected:
                    with workbook.get_sheet(name) as sheet:
                        rows = [[cell.v for cell in row] for row in sheet.rows()]
                    if rows:
                        created.append(self._create_from_rows(
                            project_id, name, rows[0], rows[1:],
                            f"Importado de {path.name}, aba {name}",
                        ))
                return created
            except Exception:
                for table_id in created:
                    self.store.delete_table(table_id)
                raise

    def preview_xlsb(self, path: str | Path, *, limit=5):
        from pyxlsb import open_workbook

        path = Path(path)
        previews = []
        with open_workbook(str(path)) as workbook:
            for name in workbook.sheets:
                with workbook.get_sheet(name) as sheet:
                    rows = []
                    for index, row in enumerate(sheet.rows()):
                        if index >= max(1, int(limit) + 1):
                            break
                        rows.append([cell.v for cell in row])
                previews.append({"sheet_name": name, "rows": rows})
        return {"file_name": path.name, "sheets": previews}

    def preview_xls(self, path: str | Path, *, limit=5):
        import xlrd

        path = Path(path)
        workbook = xlrd.open_workbook(str(path), on_demand=True)
        try:
            previews = []
            for name in workbook.sheet_names():
                sheet = workbook.sheet_by_name(name)
                rows = [sheet.row_values(index) for index in range(min(sheet.nrows, limit + 1))]
                previews.append({"sheet_name": name, "rows": rows})
            return {"file_name": path.name, "sheets": previews}
        finally:
            workbook.release_resources()

    def export_csv(self, table_id: int, path: str | Path):
        columns = self.store.list_columns(table_id)
        records = self.store.list_records(table_id)
        with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow([column["name"] for column in columns])
            for record in records:
                row = []
                for column in columns:
                    value = record["values"].get(column["name"])
                    if (
                        column["data_type"] == "text"
                        and isinstance(value, str)
                        and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                    ):
                        value = "'" + value
                    row.append(value)
                writer.writerow(row)

    def export_xlsx(self, table_id: int, path: str | Path, *, sheet_name="Dados"):
        from openpyxl import Workbook

        columns = self.store.list_columns(table_id)
        records = self.store.list_records(table_id)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_name[:31] or "Dados"
        sheet.append([column["name"] for column in columns])
        for record in records:
            row_index = sheet.max_row + 1
            for column_index, column in enumerate(columns, start=1):
                value = record["values"].get(column["name"])
                cell = sheet.cell(row=row_index, column=column_index, value=value)
                if (
                    column["data_type"] == "text"
                    and isinstance(value, str)
                    and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                ):
                    cell.data_type = "s"
        workbook.save(path)
