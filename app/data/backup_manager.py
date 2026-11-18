"""Verified SQLite backup and safe restore for the complete local PONTE store."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class BackupError(RuntimeError):
    pass


class DatabaseBackupManager:
    REQUIRED_TABLES = {"records"}

    def __init__(self, database_path):
        self.database_path = Path(database_path).expanduser().resolve()

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def inspect(cls, path, *, require_application_tables=False):
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise BackupError(f"Arquivo de banco não encontrado: {path}")
        db = None
        try:
            db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise BackupError(f"Falha de integridade SQLite: {integrity}")
            foreign_key_errors = db.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_errors:
                raise BackupError(
                    f"Banco contém {len(foreign_key_errors)} violação(ões) de chave estrangeira."
                )
            tables = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if require_application_tables:
                missing = cls.REQUIRED_TABLES - tables
                if missing:
                    raise BackupError(
                        "Backup não contém tabelas obrigatórias: " + ", ".join(sorted(missing))
                    )
            version = None
            if "ponte_schema_version" in tables:
                db.row_factory = sqlite3.Row
                version = [
                    dict(row) for row in db.execute(
                        "SELECT component, version FROM ponte_schema_version ORDER BY component"
                    ).fetchall()
                ]
            return {
                "integrity": integrity,
                "table_count": len(tables),
                "tables": sorted(tables),
                "schema_versions": version or [],
                "size_bytes": path.stat().st_size,
                "sha256": cls._hash(path),
            }
        except sqlite3.DatabaseError as exc:
            raise BackupError(f"Arquivo não é um banco SQLite válido: {exc}") from exc
        finally:
            if db is not None:
                db.close()

    def create_backup(self, destination):
        destination = Path(destination).expanduser().resolve()
        if destination == self.database_path:
            raise BackupError("O destino do backup não pode ser o banco ativo.")
        if not self.database_path.is_file():
            raise BackupError(f"Banco ativo não encontrado: {self.database_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="ponte_backup_", suffix=".sqlite3", dir=destination.parent, delete=False
        ) as temporary:
            temp_path = Path(temporary.name)
        try:
            source = sqlite3.connect(self.database_path)
            target = sqlite3.connect(temp_path)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
            details = self.inspect(temp_path)
            os.replace(temp_path, destination)
            details = self.inspect(destination)
            manifest = {
                "product": "PONTE",
                "format": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_database": self.database_path.name,
                **details,
            }
            manifest_path = destination.with_suffix(destination.suffix + ".json")
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return {"path": str(destination), "manifest": str(manifest_path), **details}
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def verify_backup(self, source):
        source = Path(source).expanduser().resolve()
        details = self.inspect(source)
        manifest_path = source.with_suffix(source.suffix + ".json")
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise BackupError(f"Manifesto do backup inválido: {exc}") from exc
            if manifest.get("sha256") != details["sha256"]:
                raise BackupError("O SHA-256 do backup não corresponde ao manifesto.")
        return details

    def restore(self, source, *, safety_backup=None):
        source = Path(source).expanduser().resolve()
        if source == self.database_path:
            raise BackupError("O arquivo de origem já é o banco ativo.")
        details = self.verify_backup(source)
        self.inspect(source, require_application_tables=True)
        if self.database_path.exists():
            if safety_backup is None:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_backup = self.database_path.with_name(
                    f"{self.database_path.stem}.antes_restauracao_{stamp}.sqlite3"
                )
            safety = self.create_backup(safety_backup)
        else:
            safety = None
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="ponte_restore_", suffix=".sqlite3",
            dir=self.database_path.parent, delete=False,
        ) as temporary:
            temp_path = Path(temporary.name)
        try:
            backup_db = sqlite3.connect(source)
            target_db = sqlite3.connect(temp_path)
            try:
                backup_db.backup(target_db)
            finally:
                target_db.close()
                backup_db.close()
            self.inspect(temp_path)
            os.replace(temp_path, self.database_path)
            restored = self.inspect(self.database_path)
            return {"restored": str(self.database_path), "safety_backup": safety, **restored}
        finally:
            if temp_path.exists():
                temp_path.unlink()
