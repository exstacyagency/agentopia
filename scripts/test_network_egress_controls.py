#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from hermes.runner import CommandRequest


class AllowRunner:
    def run(self, request: CommandRequest) -> dict:
        return {"status": "ok", "command": request.command}


class NetworkEgressControlTests(unittest.TestCase):
    def _shell_task(self, command: str, allow_network: bool) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": "task_shell_net",
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
                "permissions": {"allow_network": allow_network, "allow_memory": False, "allow_tools": False, "allowed_tool_classes": ["local_exec"], "write_scope": "none"},
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": "trace_shell_net", "submitted_at": "2026-04-15T15:00:00Z"},
        }

    def test_network_command_denied_when_allow_network_false(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("curl https://example.com", allow_network=False))
        self.assertEqual(result["result"]["error"]["code"], "NETWORK_EGRESS_DENIED")

    def test_network_command_allowed_when_allow_network_true(self) -> None:
        executor = HermesExecutor(Path.cwd(), runner=AllowRunner())
        result = executor.execute(self._shell_task("curl https://example.com", allow_network=True))
        self.assertEqual(result["run"]["status"], "succeeded")


if __name__ == "__main__":
    unittest.main()
