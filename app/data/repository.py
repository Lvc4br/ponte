from pathlib import Path

from app.data.dataset_store import DatasetStore
from app.data.sql_loader import DEFAULT_SQL, load_sql_database


class SQLRepository:
    def __init__(self):
        self.records = []
        self.source = None
        self.store = DatasetStore()

    def load(self, sql_path=DEFAULT_SQL):
        source_records = load_sql_database(sql_path)
        self.records = self.store.initialize_if_empty(source_records)
        self.source = Path(sql_path)
        return self.records

    def add_records(self, records):
        count = self.store.append(records)
        self.records = self.store.load()
        return count

    def delete_records(self, record_ids):
        count = self.store.delete(record_ids)
        self.records = self.store.load()
        return count
