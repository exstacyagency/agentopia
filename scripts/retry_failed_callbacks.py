#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "callbacks"
runs = Path(__file__).resolve().parent.parent / "var" / "hermes" / "runs"

if not base.exists():
    print("No callback records found")
    raise SystemExit(0)

for path in sorted(base.glob("*.json")):
    data = json.loads(path.read_text())
    if data.get("success") or not data.get("retryable", True):
        continue
    task_id = data.get("task_id")
    run_id = data.get("run_id")
    result_url = data.get("result_url")
    run_file = runs / f"{task_id}__{run_id}.json"
    if not run_file.exists():
        data["retryable"] = False
        data["error"] = "persisted result file missing"
        path.write_text(json.dumps(data, indent=2) + "\n")
        continue
    result_payload = json.loads(run_file.read_text()).get("result")
    req = urllib.request.Request(
        result_url,
        data=json.dumps(result_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    data["attempt_count"] = int(data.get("attempt_count", 1)) + 1
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data["success"] = True
            data["status_code"] = getattr(response, "status", None)
            data["error"] = None
    except urllib.error.HTTPError as exc:
        data["status_code"] = exc.code
        data["error"] = str(exc)
    except Exception as exc:
        data["error"] = str(exc)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"retried {path.name}: success={data.get('success')}")
