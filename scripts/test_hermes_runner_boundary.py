#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from hermes.runner import CommandRequest


class AllowRunner:
    def run(self, request: CommandRequest) -> dict:
        return {"status": "ok", "command": request.command}


class HermesRunnerBoundaryTests(unittest.TestCase):
    def _shell_task(self) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": "task_shell",
                "type": "shell_command",
                "description": "echo hi",
                "title": "shell",
                "priority": "medium",
                "risk_level": "low",
                "requester": {"id": "u1", "display_name": "u1"},
                "created_at": "2026-04-15T15:00:00Z",
                "context": {"command": "echo hi"},
            },
            "execution_policy": {
                "approval": {"required": False, "status": "approved"},
                "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 1},
                "permissions": {"allow_network": False, "allow_memory": False, "allow_tools": False, "allowed_tool_classes": ["local_exec"], "write_scope": "none"},
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": "trace_shell", "submitted_at": "2026-04-15T15:00:00Z"},
        }

    def test_shell_command_is_denied_by_default(self) -> None:
        executor = HermesExecutor(Path.cwd())
        result = executor.execute(self._shell_task())
        self.assertEqual(result["result"]["error"]["code"], "SANDBOX_DENIED")

    def test_shell_command_runs_only_through_explicit_runner(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task())
        self.assertEqual(result["run"]["status"], "succeeded")
        self.assertIn("Sandbox adapter returned", result["result"]["notes"][0])


if __name__ == "__main__":
    unittest.main()
