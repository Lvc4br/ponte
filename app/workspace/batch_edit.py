"""Atomic batch-edit operations for spreadsheet-style multi-cell changes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.workspace.store import WorkspaceStore


@dataclass(frozen=True)
class BatchEditResult:
    updated_count: int
    before: dict[int, dict[str, Any]]
    after: dict[int, dict[str, Any]]


class BatchEditError(ValueError):
    pass


class SpreadsheetBatchEditor:
    """Validate every cell first, then persist all changed rows in one transaction."""

    def __init__(self, store: WorkspaceStore):
        self.store = store

    def update_records(self, table_id: int,
                       changes: dict[int, dict[str, Any]]) -> BatchEditResult:
        if not changes:
            return BatchEditResult(0, {}, {})
        normalized_ids = [int(record_id) for record_id in changes]
        if len(normalized_ids) != len(set(normalized_ids)):
            raise BatchEditError("A seleção contém registros duplicados.")
        with self.store._connect() as db:
            columns = self.store._table_schema(db, int(table_id))
            before, after = {}, {}
            for record_id, patch in changes.items():
                row = db.execute(
                    """SELECT values_json FROM workspace_records
                       WHERE id=? AND table_id=?""",
                    (int(record_id), int(table_id)),
                ).fetchone()
                if row is None:
                    raise BatchEditError(f"Registro {record_id} não pertence à tabela.")
                current = self.store._decode(row["values_json"], {})
                before[int(record_id)] = dict(current)
                current.update(patch)
                after[int(record_id)] = self.store._normalize_values(columns, current)
            for record_id, values in after.items():
                db.execute(
                    """UPDATE workspace_records
                       SET values_json=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=? AND table_id=?""",
                    (self.store._json(values), record_id, int(table_id)),
                )
        return BatchEditResult(len(after), before, after)

    def restore(self, table_id: int,
                snapshots: dict[int, dict[str, Any]]) -> BatchEditResult:
        """Restore a prior snapshot atomically; useful for undo/redo commands."""
        return self.update_records(table_id, snapshots)
