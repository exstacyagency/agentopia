#!/usr/bin/env python3
from __future__ import annotations

import time
import unittest
from pathlib import Path

from hermes.execution_limits import enforce_execution_runtime
from hermes.executor import HermesExecutor
from hermes.runner import CommandRequest, ExecutionLimitError, SandboxAdapterRunner


class SlowAdapter:
    def run(self, request: CommandRequest) -> dict:
        time.sleep(1.2)
        return {"status": "ok", "command": request.command}


class LargeOutputExecutor(HermesExecutor):
    def _handle_text_generation(self, task_request: dict, preview_only: bool = False) -> dict:
        return {
            "summary": "large",
            "output": "x" * 4096,
            "notes": [],
            "artifacts": [],
            "tool_calls": 0,
        }


class ExecutionLimitTests(unittest.TestCase):
    def _task(self, task_type: str = "shell_command", command: str = "echo hi", runtime_minutes: int = 1, max_output_bytes: int | None = None) -> dict:
        budget = {"max_cost_usd": 1.0, "max_runtime_minutes": runtime_minutes}
        if max_output_bytes is not None:
            budget["max_output_bytes"] = max_output_bytes
        context = {"command": command} if task_type == "shell_command" else {"prompt": command}
        return {
            "schema_version": "v1",
            "task": {
                "id": "task_limits",
                "type": task_type,
                "description": command,
                "title": "limits",
                "priority": "medium",
                "risk_level": "low",
                "requester": {"id": "u1", "display_name": "u1"},
                "created_at": "2026-04-15T15:00:00Z",
                "context": context,
            },
            "execution_policy": {
                "approval": {"required": False, "status": "approved"},
                "budget": budget,
                "permissions": {"allow_network": False, "allow_memory": False, "allow_tools": False, "allowed_tool_classes": ["local_exec"], "write_scope": "none"},
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": "trace_limits", "submitted_at": "2026-04-15T15:00:00Z"},
        }

    def test_runner_enforces_runtime_limit(self) -> None:
        runner = SandboxAdapterRunner(SlowAdapter())
        with self.assertRaises(ExecutionLimitError):
            runner.run(CommandRequest(command="echo hi", cwd=Path.cwd(), max_runtime_seconds=1))

    def test_executor_runtime_limit_helper_enforces_non_runner_runtime(self) -> None:
        with self.assertRaises(ExecutionLimitError):
            with enforce_execution_runtime(1):
                time.sleep(1.2)

    def test_executor_enforces_output_size_limit(self) -> None:
        executor = LargeOutputExecutor(Path.cwd())
        payload = self._task(task_type="text_generation", command="generate", runtime_minutes=1, max_output_bytes=256)
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "EXECUTION_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
