#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from hermes.runner import CommandRequest


class AllowRunner:
    def run(self, request: CommandRequest) -> dict:
        return {"status": "ok", "command": request.command}


class DangerousActionCoverageTests(unittest.TestCase):
    def _base_task(self, task_type: str, context: dict, *, allow_network: bool = False, allowed_tool_classes: list[str] | None = None) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": f"task_{task_type}",
                "type": task_type,
                "description": "dangerous path test",
                "title": "dangerous",
                "priority": "medium",
                "risk_level": "high",
                "requester": {"id": "u1", "display_name": "u1"},
                "created_at": "2026-04-21T15:00:00Z",
                "context": context,
            },
            "execution_policy": {
                "approval": {"required": False, "status": "approved"},
                "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 1},
                "permissions": {
                    "allow_network": allow_network,
                    "allow_memory": False,
                    "allow_tools": True,
                    "allowed_tool_classes": allowed_tool_classes or [],
                    "write_scope": "none",
                },
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": f"trace_{task_type}", "submitted_at": "2026-04-21T15:00:00Z"},
        }

    def test_file_write_outside_workspace_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor = HermesExecutor(Path(tmp))
            payload = self._base_task("file_write", {"file_path": "../escape.txt", "content": "nope"}, allowed_tool_classes=["file_write"])
            result = executor.execute(payload)
            self.assertEqual(result["run"]["status"], "failed")
            self.assertEqual(result["result"]["error"]["code"], "WRITE_BOUNDARY_DENIED")

    def test_repo_write_with_out_of_bounds_change_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor = HermesExecutor(Path(tmp))
            payload = self._base_task(
                "repo_write",
                {"changes": [{"file_path": "../escape.txt", "content": "bad"}]},
                allowed_tool_classes=["repo_write"],
            )
            result = executor.execute(payload)
            self.assertEqual(result["run"]["status"], "failed")
            self.assertEqual(result["result"]["error"]["code"], "WRITE_BOUNDARY_DENIED")

    def test_shell_command_with_disallowed_syntax_is_denied(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        payload = self._base_task(
            "shell_command",
            {"command": "git status && whoami"},
            allowed_tool_classes=["local_exec"],
        )
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "SHELL_SAFETY_DENIED")

    def test_shell_command_with_network_intent_is_denied_when_network_disabled(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        payload = self._base_task(
            "shell_command",
            {"command": "curl https://example.com"},
            allow_network=False,
            allowed_tool_classes=["local_exec"],
        )
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "NETWORK_EGRESS_DENIED")

    def test_shell_command_without_local_exec_permission_is_denied(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        payload = self._base_task(
            "shell_command",
            {"command": "git status"},
            allowed_tool_classes=[],
        )
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "TOOL_PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
