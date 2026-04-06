#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperclip_adapter.client import PaperclipAdapter

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class PaperclipAdapterTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_build_plan_maps_task_to_issue_approval_and_trigger(self) -> None:
        adapter = PaperclipAdapter()
        plan = adapter.build_plan(
            self.load_fixture("task_request_valid.json"),
            company_id="company_123",
            project_id="project_123",
            goal_id="goal_123",
            execution_agent_id="agent_123",
            issue_id="ISSUE-123",
        )
        self.assertEqual(plan["task"]["task_id"], "task_123")
        self.assertEqual(plan["issue_create"]["company_id"], "company_123")
        self.assertEqual(plan["issue_create"]["project_id"], "project_123")
        self.assertEqual(plan["issue_create"]["goal_id"], "goal_123")
        self.assertEqual(plan["issue_create"]["metadata"]["agentopia"]["task_id"], "task_123")
        self.assertIsNone(plan["approval_create"])
        self.assertEqual(plan["execution_trigger"]["agent_id"], "agent_123")
        self.assertEqual(plan["execution_trigger"]["payload"]["issueId"], "ISSUE-123")

    def test_build_plan_creates_approval_when_required(self) -> None:
        adapter = PaperclipAdapter()
        payload = self.load_fixture("task_request_valid.json")
        payload["execution_policy"]["approval"] = {"required": True, "status": "pending"}
        plan = adapter.build_plan(
            payload,
            company_id="company_123",
            execution_agent_id="agent_123",
            issue_id="ISSUE-456",
        )
        self.assertIsNotNone(plan["approval_create"])
        self.assertEqual(plan["approval_create"]["approval_type"], "agentopia_task_execution")
        self.assertEqual(plan["approval_create"]["linked_issue_ids"], ["ISSUE-456"])


if __name__ == "__main__":
    unittest.main()
