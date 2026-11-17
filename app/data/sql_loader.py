from pathlib import Path
import sqlite3

from app.core.models import BridgeRecord


DEFAULT_SQL = Path(__file__).resolve().parents[2] / "database" / "ponte.sql"
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "ponte.db"


def load_sql_database(sql_path=DEFAULT_SQL, db_path=DEFAULT_DB):
    """Rebuild the local SQLite database from the user's SQL script."""
    sql_path = Path(sql_path)
    db_path = Path(db_path)
    if not sql_path.is_file():
        raise FileNotFoundError(
            f"Arquivo SQL não encontrado: {sql_path}\n"
            "Copie database/ponte.sql.example para database/ponte.sql e insira os dados."
        )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    script = sql_path.read_text(encoding="utf-8-sig")
    if not script.strip():
        raise ValueError("O arquivo SQL está vazio.")

    # Build in a temporary in-memory database first. A failed script never
    # destroys the last valid local database.
    memory = sqlite3.connect(":memory:")
    try:
        memory.executescript(script)
        tables = memory.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='obras'"
        ).fetchone()
        if not tables:
            raise ValueError("O script SQL precisa criar a tabela 'obras'.")
        columns = {row[1] for row in memory.execute("PRAGMA table_info(obras)")}
        required = {"obra", "largura_m", "compr_obra_m"}
        missing = required - columns
        if missing:
            raise ValueError("Colunas obrigatórias ausentes na tabela obras: " + ", ".join(sorted(missing)))
        rows = memory.execute("SELECT * FROM obras").fetchall()
        names = [item[0] for item in memory.execute("SELECT * FROM obras").description]
        records = [
            BridgeRecord(dict(zip(names, row)), index)
            for index, row in enumerate(rows, start=1)
        ]
        target = sqlite3.connect(db_path)
        try:
            memory.backup(target)
            target.commit()
        finally:
            target.close()
        return records
    except sqlite3.Error as exc:
        raise ValueError(f"Erro ao executar o arquivo SQL: {exc}") from exc
    finally:
        memory.close()
