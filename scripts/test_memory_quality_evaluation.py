#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class MemoryQualityEvaluationTests(unittest.TestCase):
    def test_memory_quality_evaluator_reports_expected_summary(self) -> None:
        completed = subprocess.run(
            ["./.venv/bin/python", "scripts/evaluate_memory_quality.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0)
        summary = json.loads(completed.stdout)
        self.assertEqual(summary["cases"], 3)
        self.assertEqual(summary["failed"], 0)
        names = {item["name"] for item in summary["results"]}
        self.assertIn("tenant scoped relevant recall", names)
        self.assertIn("cross tenant hit should fail evaluation", names)


if __name__ == "__main__":
    unittest.main()
