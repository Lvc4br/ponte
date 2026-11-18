"""Persistent local catalog for scanned documents and extracted sections."""

import json
import sqlite3
from pathlib import Path

from app.data.dataset_store import DEFAULT_STORE


class DocumentIndex:
    """Store document fingerprints, scan status and extracted content in SQLite."""

    def __init__(self, path=DEFAULT_STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sha256 TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    mime_type TEXT,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL,
                    errors_json TEXT NOT NULL,
                    scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    locator TEXT NOT NULL,
                    content_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_document_sections_document "
                "ON document_sections(document_id)"
            )

    def index_result(self, result) -> int:
        """Insert or refresh one scan result atomically, deduplicating by SHA-256."""
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO documents (
                    sha256, path, file_name, extension, mime_type, size_bytes,
                    status, metadata_json, warnings_json, errors_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sha256) DO UPDATE SET
                    path = excluded.path,
                    file_name = excluded.file_name,
                    extension = excluded.extension,
                    mime_type = excluded.mime_type,
                    size_bytes = excluded.size_bytes,
                    status = excluded.status,
                    metadata_json = excluded.metadata_json,
                    warnings_json = excluded.warnings_json,
                    errors_json = excluded.errors_json,
                    scanned_at = CURRENT_TIMESTAMP
                """,
                (
                    result.sha256, result.path, result.file_name, result.extension,
                    result.mime_type, result.size_bytes, result.status,
                    json.dumps(result.metadata, ensure_ascii=False, default=str),
                    json.dumps(result.warnings, ensure_ascii=False),
                    json.dumps(result.errors, ensure_ascii=False),
                ),
            )
            document_id = connection.execute(
                "SELECT id FROM documents WHERE sha256 = ?", (result.sha256,)
            ).fetchone()[0]
            connection.execute(
                "DELETE FROM document_sections WHERE document_id = ?", (document_id,)
            )
            connection.executemany(
                """
                INSERT INTO document_sections(document_id, kind, locator, content_json)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        document_id, section.kind, section.locator,
                        json.dumps(section.content, ensure_ascii=False, default=str),
                    )
                    for section in result.sections
                ],
            )
            return document_id

    def list_documents(self):
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """
                SELECT d.id, d.sha256, d.path, d.file_name, d.extension,
                       d.size_bytes, d.status, d.scanned_at,
                       COUNT(s.id) AS section_count
                FROM documents d
                LEFT JOIN document_sections s ON s.document_id = d.id
                GROUP BY d.id
                ORDER BY d.scanned_at DESC, d.id DESC
                """
            ).fetchall()
        return [
            {
                "id": row[0], "sha256": row[1], "path": row[2],
                "file_name": row[3], "extension": row[4],
                "size_bytes": row[5], "status": row[6],
                "scanned_at": row[7], "section_count": row[8],
            }
            for row in rows
        ]

    def get_document(self, document_id: int):
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT id, sha256, path, file_name, extension, mime_type,
                       size_bytes, status, metadata_json, warnings_json,
                       errors_json, scanned_at
                FROM documents WHERE id = ?
                """,
                (int(document_id),),
            ).fetchone()
            if row is None:
                return None
            sections = connection.execute(
                """
                SELECT kind, locator, content_json
                FROM document_sections WHERE document_id = ?
                ORDER BY id
                """,
                (int(document_id),),
            ).fetchall()
        return {
            "id": row[0], "sha256": row[1], "path": row[2],
            "file_name": row[3], "extension": row[4], "mime_type": row[5],
            "size_bytes": row[6], "status": row[7],
            "metadata": json.loads(row[8]), "warnings": json.loads(row[9]),
            "errors": json.loads(row[10]), "scanned_at": row[11],
            "sections": [
                {"kind": item[0], "locator": item[1], "content": json.loads(item[2])}
                for item in sections
            ],
        }
