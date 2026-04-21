#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hermes.memory.provenance import extract_memory_provenance
from paperclip.service import PaperclipService


class MemoryProvenanceTests(unittest.TestCase):
    def test_extract_memory_provenance_from_result_metadata(self) -> None:
        result = {
            "result": {
                "metadata": {
                    "memory": {
                        "tenant_id": "tenant-a",
                        "org_id": "org-a",
                        "client_id": "client-a",
                        "memory_mode": "augment",
                        "memory_source": "mempalace",
                        "memory_hits": [{"id": "m1"}, {"id": "m2"}],
                    }
                }
            }
        }
        provenance = extract_memory_provenance(result)
        self.assertEqual(provenance["tenant_id"], "tenant-a")
        self.assertEqual(provenance["memory_source"], "mempalace")
        self.assertEqual(provenance["memory_hit_count"], 2)

    def test_record_result_writes_memory_provenance_audit_event(self) -> None:
        class NoopDispatch:
            def submit(self, payload, correlation_id=None):
                return {"accepted": True}

        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=NoopDispatch())
            payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_memprov",
                    "type": "text_generation",
                    "title": "memory provenance",
                    "description": "test",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester": {"id": "u1", "display_name": "u1"},
                    "created_at": "2026-04-21T14:00:00Z",
                    "context": {"prompt": "hello"},
                },
                "execution_policy": {
                    "approval": {"required": False, "status": "approved"},
                    "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 1},
                    "permissions": {"allow_network": False, "allow_memory": True, "allow_tools": True, "allowed_tool_classes": [], "write_scope": "none"},
                    "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": False},
                },
                "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/internal", "auth_mode": "shared_token"}},
                "trace": {"trace_id": "trace_memprov", "submitted_at": "2026-04-21T14:00:00Z"},
            }
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "running")
            result = {
                "schema_version": "v1",
                "task_id": "task_memprov",
                "run": {
                    "run_id": "run_task_memprov",
                    "status": "succeeded",
                    "started_at": "2026-04-21T14:00:00Z",
                    "finished_at": "2026-04-21T14:00:01Z",
                    "runtime_seconds": 1,
                },
                "result": {
                    "summary": "ok",
                    "output_format": "markdown",
                    "output": "ok",
                    "notes": [],
                    "metadata": {
                        "memory": {
                            "tenant_id": "tenant-a",
                            "org_id": "org-a",
                            "client_id": "client-a",
                            "memory_mode": "augment",
                            "memory_source": "mempalace",
                            "memory_hits": [{"id": "m1"}],
                        }
                    },
                    "error": None,
                },
                "artifacts": [],
                "usage": {
                    "actual_cost_usd": 0.0,
                    "model_provider": "local",
                    "model_name": "test",
                    "tool_calls": 0,
                },
                "trace": {"trace_id": "trace_memprov", "reported_at": "2026-04-21T14:00:01Z"},
            }
            service.record_result("task_memprov", result)
            audit = service.get_audit("task_memprov")
            prov = [event for event in audit if event["event_type"] == "memory_provenance_recorded"]
            self.assertEqual(len(prov), 1)
            self.assertEqual(prov[0]["payload"]["memory_hit_count"], 1)
            self.assertEqual(prov[0]["payload"]["memory_source"], "mempalace")


if __name__ == "__main__":
    unittest.main()
