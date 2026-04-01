#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p artifacts
cat > artifacts/request.json <<'JSON'
{
  "task": {
    "id": "task-123",
    "title": "Summarize repo changes",
    "priority": "medium",
    "requester": {
      "id": "human",
      "displayName": "human"
    },
    "budget": {
      "maxCostUsd": 5,
      "maxRuntimeMinutes": 15
    },
    "approval": {
      "required": false
    },
    "constraints": {
      "outputFormat": "markdown",
      "outputLength": "short",
      "allowNetwork": false
    },
    "routing": {
      "inbound": "paperclip",
      "outbound": "hermes"
    }
  }
}
JSON

python3 scripts/contract-runner.py

grep -q '"status": "success"' artifacts/result.json

echo "contract demo ok"
