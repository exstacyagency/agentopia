from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "migrations"


def postgres_ddl(sql: str) -> str:
    return (
        sql.replace("TEXT PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
        .replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
        .replace("AUTOINCREMENT", "")
        .replace("datetime('now')", "CURRENT_TIMESTAMP")
    )


def available_postgres_migrations() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(path for path in MIGRATIONS_DIR.iterdir() if path.suffix == ".sql")


def apply_postgres_migrations(conn) -> list[str]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version ASC").fetchall()
    applied = {row[0] if not isinstance(row, dict) else row["version"] for row in rows}
    applied_now: list[str] = []
    for migration in available_postgres_migrations():
        if migration.name in applied:
            continue
        conn.execute(postgres_ddl(migration.read_text()))
        conn.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)",
            (migration.name,),
        )
        applied_now.append(migration.name)
    return applied_now
