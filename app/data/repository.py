from pathlib import Path

from app.data.dataset_store import DatasetStore
from app.data.sql_loader import DEFAULT_SQL, load_sql_database


class SQLRepository:
    def __init__(self):
        self.records = []
        self.source = None
        self.store = DatasetStore()
        self.records = self.store.load()

    def load(self, sql_path=DEFAULT_SQL):
        try:
            source_records = load_sql_database(sql_path)
        except Exception:
            # A previously imported/edited local dataset remains usable even if
            # the original SQL file is temporarily unavailable or invalid.
            self.records = self.store.load()
            if self.records:
                self.source = None
                return self.records
            raise
        self.records = self.store.initialize_if_empty(source_records)
        self.source = Path(sql_path)
        return self.records

    def add_records(self, records):
        count = self.store.append(records)
        self.records = self.store.load()
        return count

    def add_excel_records(self, records, file_sha256, file_name, sheet_name):
        count = self.store.append_imported_file(
            file_sha256, file_name, sheet_name, records
        )
        self.records = self.store.load()
        return count

    def delete_records(self, record_ids):
        count = self.store.delete(record_ids)
        self.records = self.store.load()
        return count
