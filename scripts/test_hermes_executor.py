#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from hermes.executor import HermesExecutor
from scripts.contracts import validate_payload

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class HermesExecutorTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_repo_summary_request_returns_valid_result(self) -> None:
        executor = HermesExecutor(ROOT)
        result = executor.execute(self.load_fixture("task_request_valid.json"))
        self.assertEqual(result["run"]["status"], "succeeded")
        errors = validate_payload("task_result_v1.json", result)
        self.assertEqual(errors, [])

    def test_invalid_request_returns_structured_failure(self) -> None:
        executor = HermesExecutor(ROOT)
        result = executor.execute(self.load_fixture("task_request_invalid.json"))
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "VALIDATION_FAILED")
        errors = validate_payload("task_result_v1.json", result)
        self.assertEqual(errors, [])

    def test_unsupported_task_type_returns_failure(self) -> None:
        executor = HermesExecutor(ROOT)
        payload = self.load_fixture("task_request_valid.json")
        payload["task"]["type"] = "text_generation"
        result = executor.execute(payload)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["result"]["error"]["code"], "EXECUTION_FAILED")
        errors = validate_payload("task_result_v1.json", result)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
