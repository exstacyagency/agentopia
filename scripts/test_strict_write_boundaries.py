#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from hermes.executor import HermesExecutor

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class StrictWriteBoundaryTests(unittest.TestCase):
    def _task(self, task_type: str, context: dict) -> dict:
        task = json.loads((FIXTURES / "task_request_valid.json").read_text())
        task["task"]["id"] = f"task_{task_type}"
        task["task"]["type"] = task_type
        task["task"]["context"] = context
        if task_type == "file_write" or task_type == "file_revert":
            task["execution_policy"]["permissions"]["allowed_tool_classes"] = ["file_write"]
        elif task_type == "repo_write":
            task["execution_policy"]["permissions"]["allowed_tool_classes"] = ["repo_write"]
        return task

    def test_file_write_rejects_path_escape(self) -> None:
        executor = HermesExecutor(Path.cwd())
        result = executor.execute(self._task("file_write", {"file_path": "../escape.txt", "content": "nope"}))
        self.assertEqual(result["result"]["error"]["code"], "WRITE_BOUNDARY_DENIED")

    def test_repo_write_rejects_path_escape(self) -> None:
        executor = HermesExecutor(Path.cwd())
        result = executor.execute(self._task("repo_write", {"changes": [{"file_path": "../escape.txt", "content": "nope"}]}))
        self.assertEqual(result["result"]["error"]["code"], "WRITE_BOUNDARY_DENIED")


if __name__ == "__main__":
    unittest.main()
