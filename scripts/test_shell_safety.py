#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from hermes.runner import CommandRequest
from hermes.shell_safety import validate_shell_command


class AllowRunner:
    def run(self, request: CommandRequest) -> dict:
        return {"status": "ok", "command": request.command}


class ShellSafetyTests(unittest.TestCase):
    def _shell_task(self, command: str) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": "task_shell_safe",
                "type": "shell_command",
                "description": command,
                "title": "shell",
                "priority": "medium",
                "risk_level": "low",
                "requester": {"id": "u1", "display_name": "u1"},
                "created_at": "2026-04-15T15:00:00Z",
                "context": {"command": command},
            },
            "execution_policy": {
                "approval": {"required": False, "status": "approved"},
                "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 1},
                "permissions": {"allow_network": False, "allow_memory": False, "allow_tools": False, "allowed_tool_classes": ["local_exec"], "write_scope": "none"},
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": "trace_shell_safe", "submitted_at": "2026-04-15T15:00:00Z"},
        }

    def test_allowlisted_simple_command_is_accepted(self) -> None:
        validate_shell_command("git status")
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("git status"))
        self.assertEqual(result["run"]["status"], "succeeded")

    def test_shell_metacharacters_are_rejected(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("git status && whoami"))
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "SHELL_SAFETY_DENIED")

    def test_disallowed_executable_is_rejected(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("python3 -c 'print(1)'"))
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "SHELL_SAFETY_DENIED")

    def test_non_allowlisted_executable_is_rejected(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("rm -rf /tmp/test"))
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "SHELL_SAFETY_DENIED")


if __name__ == "__main__":
    unittest.main()
