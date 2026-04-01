#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 <<'PY'
import pathlib
import sys

request = {
    "task": {
        "id": "task-123",
        "title": "Summarize repo changes",
        "priority": "medium",
        "requester": {
            "id": "human",
            "displayName": "human",
        },
        "budget": {
            "maxCostUsd": 5,
            "maxRuntimeMinutes": 15,
        },
        "approval": {
            "required": False,
        },
        "constraints": {
            "outputFormat": "markdown",
            "outputLength": "short",
            "allowNetwork": False,
        },
        "routing": {
            "inbound": "paperclip",
            "outbound": "hermes",
        },
    }
}

result = {
    "result": {
        "taskId": "task-123",
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

# Minimal structural validation
assert request["task"]["id"]
assert request["task"]["routing"]["inbound"] == "paperclip"
assert request["task"]["routing"]["outbound"] == "hermes"
assert result["result"]["status"] == "success"
assert result["result"]["audit"]["approvedBy"] == "paperclip"
assert result["result"]["audit"]["executedBy"] == "hermes"

print("contract demo ok")
PY
