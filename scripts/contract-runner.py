#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
REQUEST_PATH = ARTIFACTS / "request.json"
RESULT_PATH = ARTIFACTS / "result.json"

REQUIRED_REQUEST_KEYS = {
    "task": {
        "id",
        "title",
        "priority",
        "requester",
        "budget",
        "approval",
        "constraints",
        "routing",
    }
}

REQUIRED_RESULT_KEYS = {
    "result": {"taskId", "status", "summary", "artifacts", "audit"}
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require_keys(obj: dict, parent: str, keys: set[str]) -> None:
    missing = sorted(keys - set(obj.keys()))
    assert not missing, f"{parent} missing keys: {', '.join(missing)}"


def validate_request(request: dict) -> dict:
    require_keys(request, "request", {"task"})
    task = request["task"]
    require_keys(task, "task", REQUIRED_REQUEST_KEYS["task"])
    require_keys(task["requester"], "task.requester", {"id", "displayName"})
    require_keys(task["budget"], "task.budget", {"maxCostUsd", "maxRuntimeMinutes"})
    require_keys(task["approval"], "task.approval", {"required"})
    require_keys(task["constraints"], "task.constraints", {"outputFormat", "outputLength", "allowNetwork"})
    require_keys(task["routing"], "task.routing", {"inbound", "outbound"})
    assert task["routing"]["inbound"] == "paperclip"
    assert task["routing"]["outbound"] == "hermes"
    assert task["approval"]["required"] is False
    return task


def write_result(task: dict) -> None:
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
    require_keys(result, "result envelope", {"result"})
    require_keys(result["result"], "result", REQUIRED_RESULT_KEYS["result"])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")


def main() -> None:
    request = load_json(REQUEST_PATH)
    task = validate_request(request)
    write_result(task)
    print("contract runner ok")


if __name__ == "__main__":
    main()
