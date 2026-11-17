from pathlib import Path

from app.data.sql_loader import DEFAULT_DB, DEFAULT_SQL, load_sql_database


class SQLRepository:
    def __init__(self):
        self.records = []
        self.source = None
        self.database_path = Path(DEFAULT_DB)

    def load(self, sql_path=DEFAULT_SQL):
        self.records = load_sql_database(sql_path, self.database_path)
        self.source = Path(sql_path)
        return self.records
