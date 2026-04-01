#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUEST_PATH = ROOT / "artifacts" / "request.json"
RESULT_PATH = ROOT / "artifacts" / "result.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    request = load_json(REQUEST_PATH)

    task = request["task"]
    assert task["routing"]["inbound"] == "paperclip"
    assert task["routing"]["outbound"] == "hermes"
    assert task["approval"]["required"] is False

    result = {
        "result": {
            "taskId": task["id"],
            "status": "success",
            "summary": "Repository scaffold updated and documented.",
            "artifacts": ["README.md", "docs/example-flow.md"],
            "audit": {
                "approvedBy": "paperclip",
                "executedBy": "hermes",
                "runtimeSeconds": 12,
            },
        }
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print("contract runner ok")


if __name__ == "__main__":
    main()
