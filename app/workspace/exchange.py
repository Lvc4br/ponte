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

    def _create_from_rows(self, project_id, name, headers, rows, description=""):
        headers = self._unique_headers(headers)
        table_id = self.store.create_table(project_id, name, description)
        for index, header in enumerate(headers):
            values = [row[index] if index < len(row) else None for row in rows]
            data_type = self._infer_type(values)
            self.store.add_column(table_id, header, data_type, position=index)
        for row in rows:
            values = {}
            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else None
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                elif value is not None and self._infer_type(
                    [item[index] if index < len(item) else None for item in rows]
                ) == "text" and not isinstance(value, str):
                    value = str(value)
                values[header] = value
            self.store.insert_record(table_id, values)
        return table_id

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
        finally:
            workbook.close()

    def export_csv(self, table_id: int, path: str | Path):
        columns = self.store.list_columns(table_id)
        records = self.store.list_records(table_id)
        with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow([column["name"] for column in columns])
            for record in records:
                writer.writerow([record["values"].get(c["name"]) for c in columns])

    def export_xlsx(self, table_id: int, path: str | Path, *, sheet_name="Dados"):
        from openpyxl import Workbook

        columns = self.store.list_columns(table_id)
        records = self.store.list_records(table_id)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_name[:31] or "Dados"
        sheet.append([column["name"] for column in columns])
        for record in records:
            sheet.append([record["values"].get(c["name"]) for c in columns])
        workbook.save(path)
