#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.migrations import apply_migrations


class MigrationTests(unittest.TestCase):
    def test_apply_migrations_creates_schema_and_records_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            applied = apply_migrations(db_path)
            self.assertIn("001_initial_schema.sql", applied)

            conn = sqlite3.connect(db_path)
            try:
                tables = {
                    row[0]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
                self.assertIn("tasks", tables)
                self.assertIn("task_queue", tables)
                self.assertIn("task_idempotency", tables)
                self.assertIn("schema_migrations", tables)

                versions = {
                    row[0]
                    for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
                }
                self.assertIn("001_initial_schema.sql", versions)
            finally:
                conn.close()

    def test_apply_migrations_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            first = apply_migrations(db_path)
            second = apply_migrations(db_path)
            self.assertEqual(first, ["001_initial_schema.sql"])
            self.assertEqual(second, [])


if __name__ == "__main__":
    unittest.main()
