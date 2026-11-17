from pathlib import Path
import sqlite3

from app.core.models import BridgeRecord


DEFAULT_SQL = Path(__file__).resolve().parents[2] / "database" / "ponte.sql"
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "ponte.db"

# The user's source spreadsheet/SQL uses Portuguese labels with accents.
# Keep every original column and add canonical aliases used by the application.
COLUMN_ALIASES = {
    "vão_m": "vao_m",
    "vão_min_m": "vao_min_m",
    "vão_max_m": "vao_max_m",
}


def _find_source_table(connection):
    tables = {
        row[0].casefold(): row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    for candidate in ("obras", "analise_oaes"):
        if candidate in tables:
            return tables[candidate]
    raise ValueError(
        "O script SQL precisa criar uma tabela chamada 'obras' ou 'analise_oaes'."
    )


def _quote_identifier(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def load_sql_database(sql_path=DEFAULT_SQL, db_path=DEFAULT_DB):
    """Execute a local SQL script and rebuild SQLite after validating its source table."""
    sql_path = Path(sql_path)
    db_path = Path(db_path)
    if not sql_path.is_file():
        raise FileNotFoundError(
            f"Arquivo SQL não encontrado: {sql_path}\n"
            "Copie database/ponte.sql.example para database/ponte.sql e insira os dados."
        )
    script = sql_path.read_text(encoding="utf-8-sig")
    if not script.strip():
        raise ValueError("O arquivo SQL está vazio.")

    memory = sqlite3.connect(":memory:")
    try:
        memory.executescript(script)
        table = _find_source_table(memory)
        quoted_table = _quote_identifier(table)
        columns = [
            row[1] for row in memory.execute(
                f"PRAGMA table_info({quoted_table})"
            )
        ]
        folded = {name.casefold() for name in columns}
        required_groups = {
            "obra": {"obra"},
            "largura": {"largura_m"},
            "comprimento": {"compr_obra_m"},
            "vão": {"vao_m", "vão_m", "vao_min_m", "vão_min_m"},
        }
        missing = [
            label for label, alternatives in required_groups.items()
            if not (folded & {name.casefold() for name in alternatives})
        ]
        # Vão is allowed to be absent in legacy/partial records; all other
        # dimensions are required as columns, not as non-NULL values.
        missing = [label for label in missing if label != "vão"]
        if missing:
            raise ValueError(
                f"Colunas obrigatórias ausentes na tabela {table}: "
                + ", ".join(missing)
            )

        cursor = memory.execute(f"SELECT * FROM {quoted_table}")
        names = [item[0] for item in cursor.description]
        records = []
        for index, row in enumerate(cursor.fetchall(), start=1):
            values = dict(zip(names, row))
            for source, canonical in COLUMN_ALIASES.items():
                if canonical not in values and source in values:
                    values[canonical] = values[source]
            records.append(BridgeRecord(values, index))

        db_path.parent.mkdir(parents=True, exist_ok=True)
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
