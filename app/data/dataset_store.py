import json
import sqlite3
from pathlib import Path

from app.core.models import BridgeRecord
from app.data.sql_loader import APP_DIR


DEFAULT_STORE = APP_DIR / "data" / "registros.sqlite3"


class DatasetStore:
    """Persistent local dataset, independent from the original SQL source."""

    def __init__(self, path=DEFAULT_STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_excel_files (
                    sha256 TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER NOT NULL
                )
                """
            )

    def count(self):
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]

    def load(self):
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT id, payload FROM records ORDER BY id"
            ).fetchall()
        return [
            BridgeRecord(json.loads(payload), row_id)
            for row_id, payload in rows
        ]

    def initialize_if_empty(self, records):
        if self.count():
            return self.load()
        self.append(records)
        return self.load()

    def append(self, records):
        prepared = [
            (json.dumps(record.values, ensure_ascii=False, default=str),)
            for record in records
        ]
        if not prepared:
            return 0
        with sqlite3.connect(self.path) as connection:
            connection.executemany(
                "INSERT INTO records(payload) VALUES (?)", prepared
            )
        return len(prepared)

    def has_imported_file(self, sha256):
        """Return whether this exact Excel file was already imported."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT 1 FROM imported_excel_files WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
        return row is not None

    def append_imported_file(self, sha256, file_name, records):
        """Atomically append records and register the source file fingerprint."""
        prepared = [
            (json.dumps(record.values, ensure_ascii=False, default=str),)
            for record in records
        ]
        if not prepared:
            raise ValueError("A planilha não contém registros para importar.")

        try:
            with sqlite3.connect(self.path) as connection:
                connection.execute(
                    """
                    INSERT INTO imported_excel_files
                        (sha256, file_name, record_count)
                    VALUES (?, ?, ?)
                    """,
                    (sha256, file_name, len(prepared)),
                )
                connection.executemany(
                    "INSERT INTO records(payload) VALUES (?)", prepared
                )
        except sqlite3.IntegrityError as exc:
            if self.has_imported_file(sha256):
                raise ValueError(
                    f"O arquivo '{file_name}' já foi importado anteriormente. "
                    "A inclusão foi bloqueada para evitar duplicidade."
                ) from exc
            raise
        return len(prepared)

    def delete(self, record_ids):
        ids = list(dict.fromkeys(int(value) for value in record_ids))
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                f"DELETE FROM records WHERE id IN ({placeholders})", ids
            )
            return cursor.rowcount

    def backup(self):
        if not self.path.exists():
            return None
        destination = self.path.with_name(
            f"{self.path.stem}.backup{self.path.suffix}"
        )
        with sqlite3.connect(self.path) as source, sqlite3.connect(destination) as target:
            source.backup(target)
        return destination
