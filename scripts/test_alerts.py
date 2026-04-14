#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.check_alerts import evaluate_alerts


class AlertsTests(unittest.TestCase):
    def test_no_alerts_when_health_ok_and_rejections_zero(self) -> None:
        def fake_fetch_json(url: str):
            return 200, {"ok": True}

        def fake_fetch_text(url: str):
            return 200, "paperclip_requests_rejected_total 0\nhermes_requests_rejected_total 0\n"

        with patch("scripts.check_alerts.fetch_json", fake_fetch_json), patch("scripts.check_alerts.fetch_text", fake_fetch_text):
            alerts = evaluate_alerts("http://paperclip", "http://hermes")
        self.assertEqual(alerts, [])

    def test_alerts_when_health_unhealthy_and_rejections_nonzero(self) -> None:
        def fake_fetch_json(url: str):
            return 503, {"ok": False}

        def fake_fetch_text(url: str):
            return 200, "paperclip_requests_rejected_total 2\n"

        with patch("scripts.check_alerts.fetch_json", fake_fetch_json), patch("scripts.check_alerts.fetch_text", fake_fetch_text):
            alerts = evaluate_alerts("http://paperclip", "http://hermes")
        self.assertTrue(any("health endpoint unhealthy" in alert for alert in alerts))
        self.assertTrue(any("rejected request counter non-zero" in alert for alert in alerts))


if __name__ == "__main__":
    unittest.main()
