#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class OpenApiSpecTests(unittest.TestCase):
    def test_openapi_spec_contains_current_public_surface(self) -> None:
        spec = (ROOT / "openapi.yaml").read_text()
        self.assertIn("openapi: 3.1.0", spec)
        self.assertIn("/tasks:", spec)
        self.assertIn("/tasks/{taskId}:", spec)
        self.assertIn("/tasks/{taskId}/audit:", spec)
        self.assertIn("/tasks/{taskId}/cancel:", spec)
        self.assertIn("/health:", spec)
        self.assertIn("/metrics:", spec)
        self.assertIn("bearerAuth:", spec)
        self.assertIn("TaskRecord:", spec)
        self.assertIn("ApiErrorEnvelope:", spec)


if __name__ == "__main__":
    unittest.main()
