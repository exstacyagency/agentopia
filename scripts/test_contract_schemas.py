#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from contracts import validate_payload

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class ContractSchemaTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_task_request_valid_fixture_passes(self) -> None:
        payload = self.load_fixture("task_request_valid.json")
        errors = validate_payload("task_request_v1.json", payload)
        self.assertEqual(errors, [])

    def test_task_request_invalid_fixture_fails(self) -> None:
        payload = self.load_fixture("task_request_invalid.json")
        errors = validate_payload("task_request_v1.json", payload)
        self.assertGreater(len(errors), 0)

    def test_task_result_valid_fixture_passes(self) -> None:
        payload = self.load_fixture("task_result_valid.json")
        errors = validate_payload("task_result_v1.json", payload)
        self.assertEqual(errors, [])

    def test_task_result_invalid_fixture_fails(self) -> None:
        payload = self.load_fixture("task_result_invalid.json")
        errors = validate_payload("task_result_v1.json", payload)
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
