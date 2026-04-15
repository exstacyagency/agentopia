#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hermes.executor import HermesExecutor

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class HermesDispatchBoundaryTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_executor_exposes_dispatch_map_for_supported_task_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor = HermesExecutor(Path(tmp))
            self.assertEqual(set(executor._dispatch.keys()), {"repo_summary", "text_generation", "file_write", "repo_write", "file_revert", "shell_command"})

    def test_dispatch_boundary_still_returns_v1_result_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor = HermesExecutor(Path(tmp))
            task = self.load_fixture("task_request_valid.json")
            result = executor.execute(task)
            self.assertEqual(result["schema_version"], "v1")
            self.assertEqual(result["task_id"], task["task"]["id"])
            self.assertIn("run", result)
            self.assertIn("result", result)
            self.assertIn("trace", result)


if __name__ == "__main__":
    unittest.main()
