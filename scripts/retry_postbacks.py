#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paperclip_adapter.http_client import PaperclipClientConfig, PaperclipHttpClient

base = ROOT / "var" / "hermes" / "postbacks"
if not base.exists():
    print("[]")
    raise SystemExit(0)

client = PaperclipHttpClient(PaperclipClientConfig(base_url="http://127.0.0.1:3100"))
results = []
for path in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    if not data.get("retryable"):
        continue
    issue_id = data.get("issue_id")
    payload = data.get("payload") or {}
    postback_type = data.get("postback_type")
    try:
        if postback_type == "comment":
            response = client.create_issue_comment(issue_id, payload.get("body", ""))
        elif postback_type == "dashboard":
            response = client.upsert_issue_document(issue_id, payload.get("key", "agentopia-review-dashboard"), payload.get("title", "Agentopia Review Dashboard"), payload.get("body", ""))
        else:
            raise RuntimeError(f"unsupported_postback_type:{postback_type}")
        data["success"] = True
        data["retryable"] = False
        data["error"] = None
        data["replayed"] = True
        data["response"] = response
        path.write_text(json.dumps(data, indent=2) + "\n")
        results.append({"path": str(path), "status": "retried", "postback_type": postback_type})
    except Exception as exc:
        data["error"] = str(exc)
        path.write_text(json.dumps(data, indent=2) + "\n")
        results.append({"path": str(path), "status": "failed", "postback_type": postback_type, "error": str(exc)})

print(json.dumps(results, indent=2))
