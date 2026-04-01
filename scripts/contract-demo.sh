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
python3 - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('artifacts/result.json').read_text())
assert result['result']['status'] == 'success'
assert result['result']['audit']['approvedBy'] == 'paperclip'
assert result['result']['audit']['executedBy'] == 'hermes'
print('contract demo ok')
PY
