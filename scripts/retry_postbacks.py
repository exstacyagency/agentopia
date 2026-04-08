#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "postbacks"
if not base.exists():
    print("[]")
    raise SystemExit(0)

results = []
for path in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    if not data.get("retryable"):
        continue
    results.append(
        {
            "path": str(path),
            "issue_id": data.get("issue_id"),
            "run_id": data.get("run_id"),
            "postback_type": data.get("postback_type"),
            "status": "retry_not_implemented_yet",
        }
    )

print(json.dumps(results, indent=2))
