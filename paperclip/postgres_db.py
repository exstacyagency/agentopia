from __future__ import annotations

import json
from urllib.parse import urlparse

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

from scripts.migrations import apply_migrations


class PostgresPaperclipDB:
    def __init__(self, database_url: str):
        if psycopg is None:
            raise RuntimeError("psycopg is required for Postgres support")
        self.database_url = database_url
        self.conn = psycopg.connect(database_url)
        self.conn.row_factory = psycopg.rows.dict_row
        self._ensure_schema()

    def _migration_db_path(self) -> str:
        parsed = urlparse(self.database_url)
        db_name = (parsed.path or "/paperclip").removeprefix("/") or "paperclip"
        return f"/tmp/{db_name}.sqlite3"

    def _ensure_schema(self) -> None:
        apply_migrations(self._migration_db_path())
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        self.conn.commit()

    def create_task(self, record: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO tasks (
                id, schema_version, type, title, description, priority, risk_level,
                requester_id, requester_display_name, tenant_id, org_id, client_id, state, approval_status, request_payload,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record["id"],
                record["schema_version"],
                record["type"],
                record["title"],
                record["description"],
                record["priority"],
                record["risk_level"],
                record["requester_id"],
                record["requester_display_name"],
                record.get("tenant_id", ""),
                record.get("org_id", ""),
                record.get("client_id", ""),
                record["state"],
                record["approval_status"],
                json.dumps(record["request_payload"]),
                record["created_at"],
                record["updated_at"],
            ),
        )
        self.conn.commit()
