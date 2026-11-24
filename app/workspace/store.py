"""Transactional SQLite store for projects, generic tables and records.

This store shares the existing local SQLite file but never rewrites legacy
bridge records. Schema changes are additive and guarded by schema version.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.data.dataset_store import DEFAULT_STORE
from app.workspace.models import SUPPORTED_COLUMN_TYPES
from app.workspace.formulas import FormulaEngine, FormulaError


class WorkspaceStore:
    SCHEMA_VERSION = 2

    def __init__(self, path: str | Path = DEFAULT_STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS ponte_schema_version (
                    component TEXT PRIMARY KEY,
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workspace_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS workspace_tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES workspace_projects(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, name)
                );
                CREATE TABLE IF NOT EXISTS workspace_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL REFERENCES workspace_tables(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    required INTEGER NOT NULL DEFAULT 0,
                    default_json TEXT,
                    formula TEXT,
                    position INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(table_id, name)
                );
                CREATE TABLE IF NOT EXISTS workspace_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL REFERENCES workspace_tables(id) ON DELETE CASCADE,
                    values_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_workspace_records_table
                    ON workspace_records(table_id, id);
                CREATE TABLE IF NOT EXISTS workspace_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES workspace_projects(id) ON DELETE CASCADE,
                    source_table_id INTEGER NOT NULL REFERENCES workspace_tables(id) ON DELETE CASCADE,
                    source_column_id INTEGER NOT NULL REFERENCES workspace_columns(id) ON DELETE CASCADE,
                    target_table_id INTEGER NOT NULL REFERENCES workspace_tables(id) ON DELETE CASCADE,
                    target_column_id INTEGER NOT NULL REFERENCES workspace_columns(id) ON DELETE CASCADE,
                    relation_type TEXT NOT NULL DEFAULT 'many_to_one',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_column_id, target_column_id)
                );
                CREATE TABLE IF NOT EXISTS workspace_document_links (
                    project_id INTEGER NOT NULL REFERENCES workspace_projects(id) ON DELETE CASCADE,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    linked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(project_id, document_id)
                );
            """)
            row = db.execute(
                "SELECT version FROM ponte_schema_version WHERE component='workspace'"
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO ponte_schema_version(component, version) VALUES ('workspace', ?)",
                    (self.SCHEMA_VERSION,),
                )
            elif row["version"] > self.SCHEMA_VERSION:
                raise RuntimeError("O banco foi criado por uma versão mais recente do PONTE.")
            elif row["version"] < 2:
                column_names = {
                    item["name"] for item in db.execute("PRAGMA table_info(workspace_columns)")
                }
                if "formula" not in column_names:
                    db.execute("ALTER TABLE workspace_columns ADD COLUMN formula TEXT")
                db.execute(
                    "UPDATE ponte_schema_version SET version=? WHERE component='workspace'",
                    (self.SCHEMA_VERSION,),
                )

    @staticmethod
    def _name(value: str, label: str) -> str:
        name = str(value).strip()
        if not name:
            raise ValueError(f"{label} não pode ficar vazio.")
        if len(name) > 120:
            raise ValueError(f"{label} deve ter no máximo 120 caracteres.")
        return name

    @staticmethod
    def _json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Valor não pode ser serializado em JSON: {exc}") from exc

    @staticmethod
    def _decode(value: str | None, fallback=None):
        return fallback if value is None else json.loads(value)

    @staticmethod
    def _validate_value(name: str, data_type: str, value: Any, required: bool):
        if value is None:
            if required:
                raise ValueError(f"A coluna obrigatória '{name}' não pode ficar vazia.")
            return
        valid = {
            "text": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "decimal": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "date": lambda v: isinstance(v, str) and _is_date(v),
            "datetime": lambda v: isinstance(v, str) and _is_datetime(v),
            "json": lambda v: True,
        }[data_type]
        if not valid(value):
            raise ValueError(f"Valor inválido para '{name}' ({data_type}): {value!r}")

    def create_project(self, name: str, description: str = "", metadata=None) -> int:
        name = self._name(name, "Nome do projeto")
        metadata_json = self._json(metadata or {})
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO workspace_projects(name, description, metadata_json) VALUES (?, ?, ?)",
                (name, str(description), metadata_json),
            )
            return cursor.lastrowid

    def list_projects(self):
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM workspace_projects ORDER BY name COLLATE NOCASE, id"
            ).fetchall()
        return [{
            "id": r["id"], "name": r["name"], "description": r["description"],
            "metadata": self._decode(r["metadata_json"], {}),
            "created_at": r["created_at"], "updated_at": r["updated_at"],
        } for r in rows]

    def update_project(self, project_id: int, *, name=None, description=None, metadata=None):
        fields, values = [], []
        if name is not None:
            fields.append("name=?"); values.append(self._name(name, "Nome do projeto"))
        if description is not None:
            fields.append("description=?"); values.append(str(description))
        if metadata is not None:
            fields.append("metadata_json=?"); values.append(self._json(metadata))
        if not fields:
            return False
        fields.append("updated_at=CURRENT_TIMESTAMP")
        values.append(int(project_id))
        with self._connect() as db:
            cursor = db.execute(
                f"UPDATE workspace_projects SET {', '.join(fields)} WHERE id=?", values
            )
            return cursor.rowcount == 1

    def delete_project(self, project_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM workspace_projects WHERE id=?", (int(project_id),))
            return cursor.rowcount == 1

    def create_table(self, project_id: int, name: str, description: str = "") -> int:
        name = self._name(name, "Nome da tabela")
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO workspace_tables(project_id, name, description) VALUES (?, ?, ?)",
                (int(project_id), name, str(description)),
            )
            return cursor.lastrowid

    def list_tables(self, project_id: int):
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM workspace_tables WHERE project_id=? ORDER BY name COLLATE NOCASE, id",
                (int(project_id),),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_table(self, table_id: int, *, name=None, description=None) -> bool:
        fields, values = [], []
        if name is not None:
            fields.append("name=?"); values.append(self._name(name, "Nome da tabela"))
        if description is not None:
            fields.append("description=?"); values.append(str(description))
        if not fields:
            return False
        fields.append("updated_at=CURRENT_TIMESTAMP"); values.append(int(table_id))
        with self._connect() as db:
            cursor = db.execute(
                f"UPDATE workspace_tables SET {', '.join(fields)} WHERE id=?", values
            )
            return cursor.rowcount == 1

    def delete_table(self, table_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM workspace_tables WHERE id=?", (int(table_id),))
            return cursor.rowcount == 1

    def replace_tables(self, replacements) -> None:
        """Atomically replace existing tables with fully imported staging tables.

        Each item is (existing_table_id, staged_table_id, final_name). The old
        table is removed only after every replacement has been imported.
        """
        with self._connect() as db:
            for existing_id, staged_id, final_name in replacements:
                existing = db.execute(
                    "SELECT project_id FROM workspace_tables WHERE id=?",
                    (int(existing_id),),
                ).fetchone()
                staged = db.execute(
                    "SELECT project_id FROM workspace_tables WHERE id=?",
                    (int(staged_id),),
                ).fetchone()
                if existing is None or staged is None:
                    raise KeyError("Uma das tabelas da substituição não existe mais.")
                if existing["project_id"] != staged["project_id"]:
                    raise ValueError("As tabelas da substituição devem pertencer ao mesmo projeto.")
                db.execute("DELETE FROM workspace_tables WHERE id=?", (int(existing_id),))
                db.execute(
                    "UPDATE workspace_tables SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (self._name(final_name, "Nome da tabela"), int(staged_id)),
                )

    def add_column(self, table_id: int, name: str, data_type="text", *,
                   required=False, default=None, position=None, formula=None) -> int:
        name = self._name(name, "Nome da coluna")
        if data_type not in SUPPORTED_COLUMN_TYPES:
            raise ValueError(f"Tipo de coluna não suportado: {data_type}")
        if formula is not None:
            if required or default is not None:
                raise ValueError("Coluna calculada não aceita obrigatoriedade nem valor padrão.")
            if not isinstance(formula, str) or not formula.strip():
                raise ValueError("Fórmula vazia.")
        elif default is not None:
            self._validate_value(name, data_type, default, bool(required))
        with self._connect() as db:
            if formula is not None:
                existing = {
                    row["name"] for row in db.execute(
                        "SELECT name FROM workspace_columns WHERE table_id=?", (int(table_id),)
                    )
                }
                dependencies = FormulaEngine().dependencies(formula)
                missing = dependencies - existing
                if missing:
                    raise ValueError("A fórmula referencia colunas inexistentes: " + ", ".join(sorted(missing)))
                try:
                    FormulaEngine().evaluate(formula, {key: 2 for key in dependencies})
                except Exception as exc:
                    raise ValueError(f"Fórmula inválida: {exc}") from exc
            if position is None:
                position = db.execute(
                    "SELECT COALESCE(MAX(position)+1, 0) FROM workspace_columns WHERE table_id=?",
                    (int(table_id),),
                ).fetchone()[0]
            cursor = db.execute(
                """INSERT INTO workspace_columns
                   (table_id, name, data_type, required, default_json, formula, position)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (int(table_id), name, data_type, int(bool(required)),
                 None if default is None else self._json(default), formula, int(position)),
            )
            return cursor.lastrowid

    def list_columns(self, table_id: int):
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM workspace_columns WHERE table_id=? ORDER BY position, id",
                (int(table_id),),
            ).fetchall()
        return [{
            "id": r["id"], "table_id": r["table_id"], "name": r["name"],
            "data_type": r["data_type"], "required": bool(r["required"]),
            "default": self._decode(r["default_json"]), "formula": r["formula"],
            "position": r["position"],
        } for r in rows]

    def rename_column(self, column_id: int, name: str) -> bool:
        name = self._name(name, "Nome da coluna")
        with self._connect() as db:
            column = db.execute(
                "SELECT table_id, name FROM workspace_columns WHERE id=?", (int(column_id),)
            ).fetchone()
            if column is None:
                return False
            old_name = column["name"]
            dependent_formulas = db.execute(
                "SELECT name, formula FROM workspace_columns WHERE table_id=? AND formula IS NOT NULL",
                (column["table_id"],),
            ).fetchall()
            for dependent in dependent_formulas:
                if old_name in FormulaEngine().dependencies(dependent["formula"]):
                    raise ValueError(
                        f"A coluna '{old_name}' é usada pela fórmula '{dependent['name']}'."
                    )
            records = db.execute(
                "SELECT id, values_json FROM workspace_records WHERE table_id=?",
                (column["table_id"],),
            ).fetchall()
            for record in records:
                values = self._decode(record["values_json"], {})
                if old_name in values:
                    values[name] = values.pop(old_name)
                    db.execute(
                        "UPDATE workspace_records SET values_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (self._json(values), record["id"]),
                    )
            cursor = db.execute(
                "UPDATE workspace_columns SET name=? WHERE id=?",
                (name, int(column_id)),
            )
            return cursor.rowcount == 1

    def delete_column(self, column_id: int) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT table_id, name FROM workspace_columns WHERE id=?", (int(column_id),)
            ).fetchone()
            if row is None:
                return False
            table_id, name = row["table_id"], row["name"]
            for dependent in db.execute(
                "SELECT name, formula FROM workspace_columns WHERE table_id=? AND formula IS NOT NULL",
                (table_id,),
            ).fetchall():
                if name in FormulaEngine().dependencies(dependent["formula"]):
                    raise ValueError(
                        f"A coluna '{name}' é usada pela fórmula '{dependent['name']}' e não pode ser removida."
                    )
            records = db.execute(
                "SELECT id, values_json FROM workspace_records WHERE table_id=?", (table_id,)
            ).fetchall()
            for record in records:
                values = self._decode(record["values_json"], {})
                values.pop(name, None)
                db.execute(
                    "UPDATE workspace_records SET values_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (self._json(values), record["id"]),
                )
            db.execute("DELETE FROM workspace_columns WHERE id=?", (int(column_id),))
            return True

    def _table_schema(self, db, table_id: int):
        table = db.execute(
            "SELECT id FROM workspace_tables WHERE id=?", (int(table_id),)
        ).fetchone()
        if table is None:
            raise KeyError(f"Tabela {table_id} não existe.")
        return db.execute(
            "SELECT * FROM workspace_columns WHERE table_id=? ORDER BY position, id",
            (int(table_id),),
        ).fetchall()

    def _normalize_values(self, columns, values: dict[str, Any], *, partial=False):
        if not isinstance(values, dict):
            raise TypeError("Os valores do registro devem ser um dicionário.")
        schema = {c["name"]: c for c in columns}
        unknown = set(values) - set(schema)
        if unknown:
            raise ValueError("Colunas desconhecidas: " + ", ".join(sorted(unknown)))
        calculated = {name for name, column in schema.items() if column["formula"]}
        supplied_calculated = set(values) & calculated
        if supplied_calculated:
            raise ValueError("Colunas calculadas não podem ser editadas: " + ", ".join(sorted(supplied_calculated)))
        normalized = {}
        for name, column in schema.items():
            if column["formula"]:
                continue
            if name in values:
                value = values[name]
            elif partial:
                continue
            else:
                value = self._decode(column["default_json"])
            self._validate_value(name, column["data_type"], value, bool(column["required"]))
            normalized[name] = value
        return normalized

    def insert_record(self, table_id: int, values: dict[str, Any]) -> int:
        with self._connect() as db:
            columns = self._table_schema(db, table_id)
            normalized = self._normalize_values(columns, values)
            cursor = db.execute(
                "INSERT INTO workspace_records(table_id, values_json) VALUES (?, ?)",
                (int(table_id), self._json(normalized)),
            )
            return cursor.lastrowid

    def update_record(self, record_id: int, values: dict[str, Any]) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT table_id, values_json FROM workspace_records WHERE id=?",
                (int(record_id),),
            ).fetchone()
            if row is None:
                return False
            columns = self._table_schema(db, row["table_id"])
            current = self._decode(row["values_json"], {})
            current.update(values)
            normalized = self._normalize_values(columns, current)
            db.execute(
                "UPDATE workspace_records SET values_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (self._json(normalized), int(record_id)),
            )
            return True

    def delete_record(self, record_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM workspace_records WHERE id=?", (int(record_id),))
            return cursor.rowcount == 1

    def list_records(self, table_id: int, *, filters=None, sort_by=None,
                     descending=False, limit=None, offset=0):
        filters = filters or {}
        with self._connect() as db:
            columns = self._table_schema(db, table_id)
            names = {c["name"] for c in columns}
            if set(filters) - names:
                raise ValueError("Filtro usa coluna inexistente.")
            if sort_by is not None and sort_by not in names:
                raise ValueError(f"Coluna de ordenação inexistente: {sort_by}")
            rows = db.execute(
                "SELECT * FROM workspace_records WHERE table_id=? ORDER BY id",
                (int(table_id),),
            ).fetchall()
            records = [{
                "id": r["id"], "table_id": r["table_id"],
                "values": self._decode(r["values_json"], {}),
                "created_at": r["created_at"], "updated_at": r["updated_at"],
            } for r in rows]
            formula_columns = [column for column in columns if column["formula"]]
        engine = FormulaEngine()
        for record in records:
            resolved, resolving = {}, set()
            def resolve(name):
                if name in resolved:
                    return resolved[name]
                if name in resolving:
                    raise FormulaError(f"Dependência circular de fórmula: {name}")
                formula_column = next((c for c in formula_columns if c["name"] == name), None)
                if formula_column is None:
                    return record["values"].get(name)
                resolving.add(name)
                context = {
                    dependency: resolve(dependency)
                    for dependency in engine.dependencies(formula_column["formula"])
                }
                value = engine.evaluate(formula_column["formula"], context)
                self._validate_value(name, formula_column["data_type"], value, False)
                resolving.remove(name)
                resolved[name] = value
                return value
            for column in formula_columns:
                record["values"][column["name"]] = resolve(column["name"])
        for key, expected in filters.items():
            if isinstance(expected, dict):
                op, target = next(iter(expected.items()))
                operations = {
                    "eq": lambda a, b: a == b,
                    "ne": lambda a, b: a != b,
                    "contains": lambda a, b: str(b).casefold() in str(a or "").casefold(),
                    "gt": lambda a, b: a is not None and a > b,
                    "gte": lambda a, b: a is not None and a >= b,
                    "lt": lambda a, b: a is not None and a < b,
                    "lte": lambda a, b: a is not None and a <= b,
                    "in": lambda a, b: a in b,
                }
                if op not in operations:
                    raise ValueError(f"Operador de filtro não suportado: {op}")
                predicate = operations[op]
                records = [r for r in records if predicate(r["values"].get(key), target)]
            else:
                records = [r for r in records if r["values"].get(key) == expected]
        if sort_by is not None:
            records.sort(
                key=lambda r: (r["values"].get(sort_by) is None, r["values"].get(sort_by)),
                reverse=bool(descending),
            )
        start = max(0, int(offset))
        return records[start:] if limit is None else records[start:start + max(0, int(limit))]

    def create_relation(self, project_id: int, source_table_id: int,
                        source_column_id: int, target_table_id: int,
                        target_column_id: int, relation_type="many_to_one") -> int:
        allowed = {"one_to_one", "one_to_many", "many_to_one", "many_to_many"}
        if relation_type not in allowed:
            raise ValueError("Tipo de relacionamento inválido.")
        with self._connect() as db:
            source = db.execute(
                "SELECT table_id, data_type FROM workspace_columns WHERE id=?", (int(source_column_id),)
            ).fetchone()
            target = db.execute(
                "SELECT table_id, data_type FROM workspace_columns WHERE id=?", (int(target_column_id),)
            ).fetchone()
            if source is None or target is None:
                raise KeyError("Coluna de relacionamento não encontrada.")
            tables = db.execute(
                "SELECT id, project_id FROM workspace_tables WHERE id IN (?, ?)",
                (int(source_table_id), int(target_table_id)),
            ).fetchall()
            if source["table_id"] != int(source_table_id) or target["table_id"] != int(target_table_id):
                raise ValueError("As colunas precisam pertencer às tabelas informadas.")
            if source["data_type"] != target["data_type"]:
                raise ValueError("As colunas relacionadas precisam ter tipos compatíveis.")
            if len(tables) != (1 if source_table_id == target_table_id else 2):
                raise KeyError("Tabela de relacionamento não encontrada.")
            if any(row["project_id"] != int(project_id) for row in tables):
                raise ValueError("Relacionamentos só podem conectar tabelas do mesmo projeto.")
            cursor = db.execute(
                """INSERT INTO workspace_relations
                   (project_id, source_table_id, source_column_id,
                    target_table_id, target_column_id, relation_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (int(project_id), int(source_table_id), int(source_column_id),
                 int(target_table_id), int(target_column_id), relation_type),
            )
            return cursor.lastrowid

    def list_relations(self, project_id: int):
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM workspace_relations WHERE project_id=? ORDER BY id",
                (int(project_id),),
            ).fetchall()
        return [dict(r) for r in rows]

    def link_document(self, project_id: int, document_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO workspace_document_links(project_id, document_id) VALUES (?, ?)",
                (int(project_id), int(document_id)),
            )
            return cursor.rowcount == 1

    def list_project_documents(self, project_id: int):
        with self._connect() as db:
            rows = db.execute(
                """SELECT d.id, d.file_name, d.extension, d.sha256, d.status,
                          d.scanned_at, l.linked_at
                   FROM workspace_document_links l
                   JOIN documents d ON d.id=l.document_id
                   WHERE l.project_id=? ORDER BY d.file_name COLLATE NOCASE""",
                (int(project_id),),
            ).fetchall()
        return [dict(r) for r in rows]


def _is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _is_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False
