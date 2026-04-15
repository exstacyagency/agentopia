#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paperclip.db import PaperclipDB


class FakePostgresDB:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = object()

    def create_task(self, record: dict) -> None:
        self.last_task = record


class PostgresPersistenceTests(unittest.TestCase):
    def test_postgres_url_selects_postgres_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            os.environ["PAPERCLIP_DATABASE_URL"] = "postgresql://agentopia:secret@localhost:5432/agentopia"
            with patch("paperclip.db.PostgresPaperclipDB", FakePostgresDB):
                db = PaperclipDB(db_path)
                self.assertIsInstance(db, FakePostgresDB)
                self.assertEqual(db.database_url, os.environ["PAPERCLIP_DATABASE_URL"])
        os.environ.pop("PAPERCLIP_DATABASE_URL", None)

    def test_postgres_backend_exposes_expected_helper_surface(self) -> None:
        expected_methods = {
            "run_in_transaction",
            "create_task",
            "get_task",
            "update_task_state",
            "add_audit_event",
            "get_audit_events",
            "list_tasks",
            "enqueue_task",
            "claim_queue_item",
            "mark_queue_running",
            "mark_queue_timed_out",
            "reset_queue_to_queued",
            "mark_queue_retry",
            "mark_queue_dead_letter",
            "mark_queue_dispatched",
            "get_queue_item",
            "list_queue_items",
            "create_idempotency_record",
            "get_idempotent_task_id",
            "store_result",
            "get_result",
            "delete_task_data",
            "transition_task_with_audit",
            "store_result_with_audit",
        }
        from paperclip import postgres_db

        self.assertTrue(expected_methods.issubset(set(dir(postgres_db.PostgresPaperclipDB))))


if __name__ == "__main__":
    unittest.main()
