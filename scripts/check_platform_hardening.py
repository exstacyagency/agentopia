#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

checks = {
    "issue_action_endpoint": (ROOT / "hermes" / "issue_actions.py").exists(),
    "dashboard_state_endpoint": (ROOT / "hermes" / "dashboard_state.py").exists(),
    "runtime_guards": (ROOT / "hermes" / "runtime_checks.py").exists(),
    "review_dashboard_doc": (ROOT / "docs" / "paperclip-hermes-ui-facing-dashboard.md").exists(),
}

print(json.dumps({
    "ok": all(checks.values()),
    "checks": checks,
}, indent=2))
