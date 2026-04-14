#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from io import StringIO
from unittest.mock import patch

from scripts.structured_logging import log_event


class StructuredLoggingTests(unittest.TestCase):
    def test_log_event_emits_json(self) -> None:
        stream = StringIO()
        with patch("sys.stdout", stream):
            log_event("paperclip", "request_received", path="/tasks", method="POST")
        line = stream.getvalue().strip()
        payload = json.loads(line)
        self.assertEqual(payload["service"], "paperclip")
        self.assertEqual(payload["event"], "request_received")
        self.assertEqual(payload["path"], "/tasks")
        self.assertEqual(payload["method"], "POST")
        self.assertIn("timestamp", payload)


if __name__ == "__main__":
    unittest.main()
