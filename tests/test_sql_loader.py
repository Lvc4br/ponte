import sqlite3

import pytest

from app.data.sql_loader import load_sql_database


def test_load_sql_script_and_rebuild_database(tmp_path):
    sql = tmp_path / "ponte.sql"
    db = tmp_path / "data" / "ponte.db"
    sql.write_text("""
        CREATE TABLE obras (
            id INTEGER PRIMARY KEY,
            obra INTEGER NOT NULL,
            tipo_obra TEXT,
            largura_m REAL,
            vao_min_m REAL,
            vao_max_m REAL,
            compr_obra_m REAL,
            em_m3_m2 REAL
        );
        INSERT INTO obras (obra, tipo_obra, largura_m, vao_min_m, vao_max_m, compr_obra_m, em_m3_m2)
        VALUES (7, 'Ponte', 12, 40, 42, 100, 0.45);
    """, encoding="utf-8")

    records = load_sql_database(sql, db)
    assert len(records) == 1
    assert records[0].get("obra") == 7
    assert records[0].get("vao_min_m") == 40
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM obras").fetchone()[0] == 1


def test_missing_sql_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_sql_database(tmp_path / "missing.sql", tmp_path / "db.sqlite")


def test_requires_obras_table(tmp_path):
    sql = tmp_path / "invalid.sql"
    sql.write_text("CREATE TABLE outra (id INTEGER);", encoding="utf-8")
    with pytest.raises(ValueError, match="tabela 'obras'"):
        load_sql_database(sql, tmp_path / "db.sqlite")
