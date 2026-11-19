"""Local document governance primitives for PONTE.

This module provides append-only audit events, immutable revision snapshots,
approval records and role/permission checks. It is a local foundation, not an
authentication server: callers must supply a trusted actor identity. Do not
treat a username passed by the desktop UI as proof of identity.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.dataset_store import DEFAULT_STORE


ROLE_PERMISSIONS = {
    "viewer": frozenset({"workspace.read", "documents.read"}),
    "editor": frozenset({"workspace.read", "workspace.edit", "documents.read", "documents.review"}),
    "approver": frozenset({"workspace.read", "documents.read", "documents.review", "documents.approve"}),
    "administrator": frozenset({
        "workspace.read", "workspace.edit", "documents.read", "documents.review",
        "documents.approve", "users.manage", "governance.manage",
    }),
}


class GovernanceError(ValueError):
    """Raised when a governance operation violates its workflow."""


class GovernanceStore:
    """Persist audit, revision, approval and role data in the PONTE SQLite file."""

    def __init__(self, path: str | Path = DEFAULT_STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS governance_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    previous_hash TEXT,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE INDEX IF NOT EXISTS idx_governance_audit_entity
                    ON governance_audit(entity_type, entity_id, id);
                CREATE TABLE IF NOT EXISTS governance_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    comment TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    UNIQUE(entity_type, entity_id, revision)
                );
                CREATE TABLE IF NOT EXISTS governance_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
                    requested_by TEXT NOT NULL,
                    reviewed_by TEXT,
                    comment TEXT NOT NULL DEFAULT '',
                    requested_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    UNIQUE(entity_type, entity_id, revision)
                );
                CREATE TABLE IF NOT EXISTS governance_roles (
                    actor TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK(role IN ('viewer','editor','approver','administrator')),
                    updated_at TEXT NOT NULL
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        return db

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, default=str)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _required(value: str, label: str) -> str:
        value = str(value).strip()
        if not value:
            raise GovernanceError(f"{label} é obrigatório.")
        if len(value) > 200:
            raise GovernanceError(f"{label} excede 200 caracteres.")
        return value

    def set_role(self, actor: str, role: str, *, changed_by: str) -> None:
        actor = self._required(actor, "Usuário")
        changed_by = self._required(changed_by, "Responsável pela alteração")
        if role not in ROLE_PERMISSIONS:
            raise GovernanceError(f"Perfil inválido: {role}")
        now = self._now()
        with self._connect() as db:
            db.execute(
                """INSERT INTO governance_roles(actor, role, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(actor) DO UPDATE SET role=excluded.role, updated_at=excluded.updated_at""",
                (actor, role, now),
            )
        self.record_event(changed_by, "role.assigned", "user", actor, {"role": role})

    def role_for(self, actor: str) -> str:
        with self._connect() as db:
            row = db.execute("SELECT role FROM governance_roles WHERE actor=?", (actor,)).fetchone()
        return row["role"] if row else "viewer"

    def has_permission(self, actor: str, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS[self.role_for(actor)]

    def require_permission(self, actor: str, permission: str) -> None:
        if not self.has_permission(actor, permission):
            raise GovernanceError(f"Usuário sem permissão: {permission}")

    def record_event(self, actor: str, action: str, entity_type: str,
                     entity_id: str | int, details: Any | None = None) -> int:
        actor = self._required(actor, "Usuário")
        action = self._required(action, "Ação")
        entity_type = self._required(entity_type, "Tipo de entidade")
        entity_id = self._required(str(entity_id), "Identificador")
        payload = self._json(details or {})
        now = self._now()
        with self._connect() as db:
            previous = db.execute(
                "SELECT event_hash FROM governance_audit ORDER BY id DESC LIMIT 1"
            ).fetchone()
            previous_hash = previous["event_hash"] if previous else None
            import hashlib
            material = self._json([now, actor, action, entity_type, entity_id, payload, previous_hash])
            event_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
            cursor = db.execute(
                """INSERT INTO governance_audit
                   (occurred_at, actor, action, entity_type, entity_id, details_json, previous_hash, event_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (now, actor, action, entity_type, entity_id, payload, previous_hash, event_hash),
            )
            return int(cursor.lastrowid)

    def list_events(self, entity_type: str | None = None, entity_id: str | int | None = None):
        clauses, params = [], []
        if entity_type is not None:
            clauses.append("entity_type=?"); params.append(entity_type)
        if entity_id is not None:
            clauses.append("entity_id=?"); params.append(str(entity_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM governance_audit" + where + " ORDER BY id",
                params,
            ).fetchall()
        return [{
            "id": row["id"], "occurred_at": row["occurred_at"], "actor": row["actor"],
            "action": row["action"], "entity_type": row["entity_type"],
            "entity_id": row["entity_id"], "details": json.loads(row["details_json"]),
            "previous_hash": row["previous_hash"], "event_hash": row["event_hash"],
        } for row in rows]

    def verify_audit_chain(self) -> bool:
        import hashlib
        previous_hash = None
        for event in self.list_events():
            material = self._json([
                event["occurred_at"], event["actor"], event["action"],
                event["entity_type"], event["entity_id"],
                self._json(event["details"]), previous_hash,
            ])
            expected = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if event["previous_hash"] != previous_hash or event["event_hash"] != expected:
                return False
            previous_hash = event["event_hash"]
        return True

    def save_revision(self, entity_type: str, entity_id: str | int, snapshot: Any,
                      *, actor: str, comment: str = "") -> int:
        entity_type = self._required(entity_type, "Tipo de entidade")
        entity_id = self._required(str(entity_id), "Identificador")
        actor = self._required(actor, "Usuário")
        snapshot_json = self._json(snapshot)
        now = self._now()
        with self._connect() as db:
            revision = db.execute(
                """SELECT COALESCE(MAX(revision), 0) + 1 FROM governance_revisions
                   WHERE entity_type=? AND entity_id=?""",
                (entity_type, entity_id),
            ).fetchone()[0]
            cursor = db.execute(
                """INSERT INTO governance_revisions
                   (entity_type, entity_id, revision, snapshot_json, actor, comment, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (entity_type, entity_id, revision, snapshot_json, actor, str(comment), now),
            )
        self.record_event(actor, "revision.created", entity_type, entity_id, {"revision": revision})
        return int(revision)

    def list_revisions(self, entity_type: str, entity_id: str | int):
        with self._connect() as db:
            rows = db.execute(
                """SELECT revision, snapshot_json, actor, comment, created_at
                   FROM governance_revisions WHERE entity_type=? AND entity_id=? ORDER BY revision DESC""",
                (entity_type, str(entity_id)),
            ).fetchall()
        return [{
            "revision": row["revision"], "snapshot": json.loads(row["snapshot_json"]),
            "actor": row["actor"], "comment": row["comment"], "created_at": row["created_at"],
        } for row in rows]

    def request_approval(self, entity_type: str, entity_id: str | int, revision: int,
                         *, requested_by: str) -> int:
        entity_type = self._required(entity_type, "Tipo de entidade")
        entity_id = self._required(str(entity_id), "Identificador")
        requested_by = self._required(requested_by, "Solicitante")
        now = self._now()
        with self._connect() as db:
            exists = db.execute(
                """SELECT 1 FROM governance_revisions
                   WHERE entity_type=? AND entity_id=? AND revision=?""",
                (entity_type, entity_id, int(revision)),
            ).fetchone()
            if not exists:
                raise GovernanceError("A revisão solicitada não existe.")
            try:
                cursor = db.execute(
                    """INSERT INTO governance_approvals
                       (entity_type, entity_id, revision, status, requested_by, requested_at)
                       VALUES (?, ?, ?, 'pending', ?, ?)""",
                    (entity_type, entity_id, int(revision), requested_by, now),
                )
            except sqlite3.IntegrityError as exc:
                raise GovernanceError("Esta revisão já possui solicitação de aprovação.") from exc
        self.record_event(requested_by, "approval.requested", entity_type, entity_id, {"revision": int(revision)})
        return int(cursor.lastrowid)

    def review_approval(self, approval_id: int, decision: str, *, reviewer: str,
                        comment: str = "") -> bool:
        reviewer = self._required(reviewer, "Aprovador")
        if decision not in {"approved", "rejected"}:
            raise GovernanceError("Decisão deve ser approved ou rejected.")
        with self._connect() as db:
            row = db.execute(
                "SELECT entity_type, entity_id, revision, status FROM governance_approvals WHERE id=?",
                (int(approval_id),),
            ).fetchone()
            if row is None:
                raise GovernanceError("Solicitação de aprovação não encontrada.")
            if row["status"] != "pending":
                raise GovernanceError("A solicitação já foi analisada.")
            db.execute(
                """UPDATE governance_approvals SET status=?, reviewed_by=?, comment=?, reviewed_at=?
                   WHERE id=? AND status='pending'""",
                (decision, reviewer, str(comment), self._now(), int(approval_id)),
            )
        self.record_event(
            reviewer, "approval." + decision, row["entity_type"], row["entity_id"],
            {"revision": row["revision"], "approval_id": int(approval_id), "comment": str(comment)},
        )
        return True

    def list_approvals(self, status: str | None = None):
        with self._connect() as db:
            if status is None:
                rows = db.execute("SELECT * FROM governance_approvals ORDER BY id DESC").fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM governance_approvals WHERE status=? ORDER BY id DESC", (status,)
                ).fetchall()
        return [dict(row) for row in rows]
