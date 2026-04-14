#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hermes.persistence import HermesPersistence


class PersistenceRedactionTests(unittest.TestCase):
    def test_persist_result_redacts_sensitive_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            persistence = HermesPersistence(root)
            result = {
                "task_id": "task_123",
                "run": {"run_id": "run_task_123", "status": "succeeded"},
                "result": {
                    "summary": "ok",
                    "metadata": {
                        "api_key": "super-secret-key",
                        "authToken": "token-value",
                        "nested": {
                            "password": "hunter2",
                        },
                    },
                },
            }
            path = persistence.persist_result(result)
            payload = json.loads(path.read_text())
            metadata = payload["result"]["result"]["metadata"]
            self.assertEqual(metadata["api_key"], "[REDACTED]")
            self.assertEqual(metadata["authToken"], "[REDACTED]")
            self.assertEqual(metadata["nested"]["password"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
