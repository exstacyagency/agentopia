#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request

EXPECTED_FEATURES = {
    "issue_action_endpoint",
    "dashboard_state_endpoint",
    "runtime_guard_health",
    "paperclip_http_diagnostics",
}

with urllib.request.urlopen("http://127.0.0.1:3200/health", timeout=10) as response:
    data = json.loads(response.read().decode())

build = data.get("build") or {}
features = set(build.get("features") or [])
missing = sorted(EXPECTED_FEATURES - features)

print(json.dumps({
    "ok": not missing,
    "build_stamp": build.get("stamp"),
    "features": sorted(features),
    "missing_features": missing,
}, indent=2))
