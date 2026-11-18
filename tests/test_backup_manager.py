import json
from pathlib import Path
import sqlite3

import pytest

from app.data.backup_manager import BackupError, DatabaseBackupManager


def create_database(path, value="original"):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
        db.execute("INSERT INTO records(payload) VALUES (?)", (value,))


def read_value(path):
    with sqlite3.connect(path) as db:
        return db.execute("SELECT payload FROM records WHERE id=1").fetchone()[0]


def test_backup_contains_consistent_sqlite_snapshot_and_manifest(tmp_path):
    active = tmp_path / "active.sqlite3"
    create_database(active)
    manager = DatabaseBackupManager(active)
    destination = tmp_path / "backup.sqlite3"
    result = manager.create_backup(destination)
    assert result["integrity"] == "ok"
    assert result["sha256"]
    assert destination.is_file()
    assert destination.with_suffix(".sqlite3.json").is_file()
    assert manager.verify_backup(destination)["integrity"] == "ok"


def test_restore_creates_safety_backup_and_restores_snapshot(tmp_path):
    active = tmp_path / "active.sqlite3"
    create_database(active)
    manager = DatabaseBackupManager(active)
    backup = tmp_path / "backup.sqlite3"
    manager.create_backup(backup)
    with sqlite3.connect(active) as db:
        db.execute("UPDATE records SET payload='alterado' WHERE id=1")
    result = manager.restore(backup)
    assert read_value(active) == "original"
    assert result["integrity"] == "ok"
    assert result["safety_backup"] is not None
    assert Path(result["safety_backup"]["path"]).is_file()


def test_tampered_backup_manifest_is_rejected(tmp_path):
    active = tmp_path / "active.sqlite3"
    create_database(active)
    manager = DatabaseBackupManager(active)
    backup = tmp_path / "backup.sqlite3"
    manager.create_backup(backup)
    manifest_path = backup.with_suffix(".sqlite3.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BackupError):
        manager.verify_backup(backup)


def test_invalid_restore_does_not_change_active_database(tmp_path):
    active = tmp_path / "active.sqlite3"
    create_database(active)
    invalid = tmp_path / "invalid.sqlite3"
    invalid.write_text("not sqlite", encoding="utf-8")
    with pytest.raises(BackupError):
        DatabaseBackupManager(active).restore(invalid)
    assert read_value(active) == "original"
