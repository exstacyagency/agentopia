#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import time
import unittest
from pathlib import Path

from paperclip.db import PaperclipDB

ROOT = Path(__file__).resolve().parent.parent
CONTAINER = "agentopia-test-postgres"
URL = "postgresql://agentopia:agentopia@127.0.0.1:55432/agentopia"


class PostgresLiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["docker", "rm", "-f", CONTAINER], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                CONTAINER,
                "-e",
                "POSTGRES_PASSWORD=agentopia",
                "-e",
                "POSTGRES_USER=agentopia",
                "-e",
                "POSTGRES_DB=agentopia",
                "-p",
                "55432:5432",
                "postgres:16-alpine",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        for _ in range(30):
            result = subprocess.run(
                ["docker", "exec", CONTAINER, "pg_isready", "-U", "agentopia"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError("Postgres test container did not become ready")

    @classmethod
    def tearDownClass(cls) -> None:
        subprocess.run(["docker", "rm", "-f", CONTAINER], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_postgres_backend_can_create_and_read_task(self) -> None:
        os.environ["PAPERCLIP_DATABASE_URL"] = URL
        try:
            db = PaperclipDB(ROOT / "data" / "paperclip.sqlite3")
            db.create_task(
                {
                    "id": "task_pg_live",
                    "schema_version": "v1",
                    "type": "repo_summary",
                    "title": "pg live",
                    "description": "pg live",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester_id": "u1",
                    "requester_display_name": "u1",
                    "tenant_id": "",
                    "org_id": "",
                    "client_id": "",
                    "state": "received",
                    "approval_status": "approved",
                    "request_payload": {"trace": {"trace_id": "trace_pg_live"}},
                    "created_at": "2026-04-15T15:00:00Z",
                    "updated_at": "2026-04-15T15:00:00Z",
                }
            )
            task = db.get_task("task_pg_live")
            self.assertIsNotNone(task)
            self.assertEqual(task["id"], "task_pg_live")
        finally:
            os.environ.pop("PAPERCLIP_DATABASE_URL", None)


if __name__ == "__main__":
    unittest.main()
