#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from hermes.executor import HermesExecutor

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class ToolPermissionTests(unittest.TestCase):
    def _task(self, task_type: str, allowed_tool_classes: list[str], context: dict | None = None) -> dict:
        task = json.loads((FIXTURES / "task_request_valid.json").read_text())
        task["task"]["id"] = f"task_{task_type}"
        task["task"]["type"] = task_type
        task["task"]["context"] = context or {}
        task["execution_policy"]["permissions"]["allowed_tool_classes"] = allowed_tool_classes
        return task

    def test_repo_write_denied_when_tool_class_not_allowed(self) -> None:
        executor = HermesExecutor(Path.cwd())
        result = executor.execute(self._task("repo_write", ["repo_read"], context={"changes": []}))
        self.assertEqual(result["result"]["error"]["code"], "TOOL_PERMISSION_DENIED")

    def test_repo_write_allowed_when_tool_class_is_present(self) -> None:
        executor = HermesExecutor(Path.cwd())
        result = executor.execute(
            self._task(
                "repo_write",
                ["repo_write"],
                context={"changes": [{"file_path": "tmp_tool_permission_test.txt", "content": "ok"}]},
            )
        )
        self.assertEqual(result["run"]["status"], "succeeded")
        target = Path.cwd() / "tmp_tool_permission_test.txt"
        if target.exists():
            target.unlink()


if __name__ == "__main__":
    unittest.main()
