#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from hermes.memory.service import MemPalaceService


class DisabledMemoryService:
    def wakeup(self, scope_payload: dict, issue_title: str, issue_description: str) -> dict:
        return {
            "scope": scope_payload,
            "config": {},
            "ok": False,
            "reason": "mempalace_disabled",
            "memory_mode": "augment",
            "fallback_reason": "mempalace_disabled",
            "wakeup_context": {
                "issue_title": issue_title,
                "issue_description": issue_description,
                "memory_hits": [],
                "memory_source": "native_only",
            },
        }


class MemoryFallbackTests(unittest.TestCase):
    def _task(self) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": "task_memfallback",
                "type": "text_generation",
                "description": "Generate text",
                "title": "memory fallback test",
                "priority": "medium",
                "risk_level": "low",
                "requester": {"id": "u1", "display_name": "u1"},
                "tenant": {"tenant_id": "tenant-a", "org_id": "org-a", "client_id": "client-a"},
                "created_at": "2026-04-21T14:00:00Z",
                "context": {"prompt": "hello"},
            },
            "execution_policy": {
                "approval": {"required": False, "status": "approved"},
                "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 1},
                "permissions": {"allow_network": False, "allow_memory": True, "allow_tools": True, "allowed_tool_classes": ["local_exec"], "write_scope": "none"},
                "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
            },
            "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
            "trace": {"trace_id": "trace_memfallback", "submitted_at": "2026-04-21T14:00:00Z"},
        }

    def test_runtime_falls_back_to_native_only_when_mempalace_unavailable(self) -> None:
        executor = HermesExecutor(Path.cwd(), memory_service=DisabledMemoryService())
        result = executor.execute(self._task())
        self.assertEqual(result["run"]["status"], "succeeded")
        memory = result["result"]["metadata"]["memory"]
        self.assertEqual(memory["memory_source"], "native_only")
        self.assertEqual(memory["fallback_reason"], "mempalace_disabled")
        self.assertEqual(memory["memory_hits"], [])


if __name__ == "__main__":
    unittest.main()
