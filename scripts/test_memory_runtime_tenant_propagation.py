#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from hermes.executor import HermesExecutor


class ScopedMemoryService:
    def wakeup(self, scope_payload: dict, issue_title: str, issue_description: str) -> dict:
        tenant_id = scope_payload["tenant_id"]
        return {
            "scope": scope_payload,
            "config": {},
            "ok": True,
            "reason": "mempalace_search_ok",
            "memory_mode": "augment",
            "wakeup_context": {
                "issue_title": issue_title,
                "issue_description": issue_description,
                "memory_hits": [{"tenant_id": tenant_id, "memory": f"hit-for-{tenant_id}"}],
                "memory_source": "mempalace",
            },
        }


class MemoryRuntimeTenantPropagationTests(unittest.TestCase):
    def _task(self, tenant_id: str) -> dict:
        return {
            "schema_version": "v1",
            "task": {
                "id": f"task_{tenant_id}",
                "type": "text_generation",
                "description": "Generate text",
                "title": "tenant aware memory test",
                "priority": "medium",
                "risk_level": "low",
                "requester": {"id": "u1", "display_name": "u1"},
                "tenant": {"tenant_id": tenant_id, "org_id": f"org-{tenant_id}", "client_id": f"client-{tenant_id}"},
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
            "trace": {"trace_id": f"trace_{tenant_id}", "submitted_at": "2026-04-21T14:00:00Z"},
        }

    def test_runtime_memory_metadata_uses_task_tenant_scope(self) -> None:
        executor = HermesExecutor(Path.cwd(), memory_service=ScopedMemoryService())
        result_a = executor.execute(self._task("tenant-a"))
        result_b = executor.execute(self._task("tenant-b"))

        memory_a = result_a["result"]["metadata"]["memory"]
        memory_b = result_b["result"]["metadata"]["memory"]

        self.assertEqual(memory_a["tenant_id"], "tenant-a")
        self.assertEqual(memory_b["tenant_id"], "tenant-b")
        self.assertEqual(memory_a["memory_hits"][0]["tenant_id"], "tenant-a")
        self.assertEqual(memory_b["memory_hits"][0]["tenant_id"], "tenant-b")
        self.assertNotEqual(memory_a["memory_hits"], memory_b["memory_hits"])

    def test_memory_is_not_used_without_allow_memory(self) -> None:
        payload = self._task("tenant-a")
        payload["execution_policy"]["permissions"]["allow_memory"] = False
        executor = HermesExecutor(Path.cwd(), memory_service=ScopedMemoryService())
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "succeeded")
        self.assertEqual(result["result"].get("metadata", {}), {})


if __name__ == "__main__":
    unittest.main()
