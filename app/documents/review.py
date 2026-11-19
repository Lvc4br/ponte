"""Human review queue for values extracted from source documents.

Extraction is evidence, not engineering approval. Every candidate retains its
source fingerprint and locator and remains pending until a reviewer decides.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.data.dataset_store import DEFAULT_STORE


class ReviewError(ValueError):
    pass


class ExtractionReviewStore:
    STATUSES = {"pending", "approved", "rejected", "corrected"}

    def __init__(self, path: str | Path = DEFAULT_STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS extraction_review_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_sha256 TEXT NOT NULL,
                    document_path TEXT NOT NULL,
                    source_locator TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    extracted_value_json TEXT NOT NULL,
                    reviewed_value_json TEXT,
                    confidence REAL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending','approved','rejected','corrected')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    review_comment TEXT NOT NULL DEFAULT '',
                    UNIQUE(document_sha256, source_locator, field_name)
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_extraction_review_status
                ON extraction_review_items(status, created_at)
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        return db

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, default=str)

    def submit(self, *, document_sha256: str, document_path: str,
               source_locator: str, field_name: str, extracted_value: Any,
               confidence: float | None = None) -> int:
        required = {
            "SHA-256": document_sha256, "Caminho do documento": document_path,
            "Localizador da origem": source_locator, "Campo": field_name,
        }
        for label, value in required.items():
            if not str(value).strip():
                raise ReviewError(f"{label} é obrigatório.")
        if confidence is not None and not 0 <= float(confidence) <= 1:
            raise ReviewError("Confiança deve estar entre 0 e 1.")
        with self._connect() as db:
            db.execute(
                """INSERT INTO extraction_review_items
                   (document_sha256, document_path, source_locator, field_name,
                    extracted_value_json, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(document_sha256, source_locator, field_name)
                   DO UPDATE SET document_path=excluded.document_path,
                     extracted_value_json=excluded.extracted_value_json,
                     confidence=excluded.confidence,
                     status='pending', reviewed_value_json=NULL,
                     reviewed_at=NULL, reviewed_by=NULL, review_comment=''""",
                (str(document_sha256), str(document_path), str(source_locator),
                 str(field_name), self._json(extracted_value), confidence),
            )
            row = db.execute(
                """SELECT id FROM extraction_review_items
                   WHERE document_sha256=? AND source_locator=? AND field_name=?""",
                (str(document_sha256), str(source_locator), str(field_name)),
            ).fetchone()
            return int(row["id"])

    def list_items(self, status: str | None = "pending"):
        if status is not None and status not in self.STATUSES:
            raise ReviewError(f"Status inválido: {status}")
        with self._connect() as db:
            if status is None:
                rows = db.execute(
                    "SELECT * FROM extraction_review_items ORDER BY created_at DESC, id DESC"
                ).fetchall()
            else:
                rows = db.execute(
                    """SELECT * FROM extraction_review_items
                       WHERE status=? ORDER BY created_at DESC, id DESC""",
                    (status,),
                ).fetchall()
        return [self._decode(row) for row in rows]

    def get_item(self, item_id: int):
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM extraction_review_items WHERE id=?", (int(item_id),)
            ).fetchone()
        return None if row is None else self._decode(row)

    @staticmethod
    def _decode(row):
        item = dict(row)
        item["extracted_value"] = json.loads(item.pop("extracted_value_json"))
        raw_reviewed = item.pop("reviewed_value_json")
        item["reviewed_value"] = None if raw_reviewed is None else json.loads(raw_reviewed)
        return item

    def review(self, item_id: int, decision: str, *, reviewer: str,
               comment: str = "", corrected_value: Any = None) -> bool:
        if decision not in {"approved", "rejected", "corrected"}:
            raise ReviewError("Decisão deve ser approved, rejected ou corrected.")
        if not str(reviewer).strip():
            raise ReviewError("Revisor é obrigatório.")
        if decision == "corrected" and corrected_value is None:
            raise ReviewError("Informe o valor corrigido.")
        reviewed_json = self._json(corrected_value) if decision == "corrected" else None
        with self._connect() as db:
            cursor = db.execute(
                """UPDATE extraction_review_items
                   SET status=?, reviewed_value_json=?, reviewed_at=CURRENT_TIMESTAMP,
                       reviewed_by=?, review_comment=?
                   WHERE id=? AND status='pending'""",
                (decision, reviewed_json, str(reviewer).strip(), str(comment),
                 int(item_id)),
            )
            if cursor.rowcount != 1:
                raise ReviewError("Item não encontrado ou já revisado.")
        return True
