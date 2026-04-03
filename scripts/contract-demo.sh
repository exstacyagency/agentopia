#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/sample-task.sh
python3 scripts/task-runner.py
python3 - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('artifacts/result.json').read_text())
output = json.loads(Path('artifacts/output.json').read_text())
fixture = json.loads(Path('scripts/output_fixture.json').read_text())
assert result['result']['status'] == 'success'
assert result['result']['audit']['approvedBy'] == 'paperclip'
assert result['result']['audit']['executedBy'] == 'hermes'
assert output == fixture
assert Path('artifacts/summary.txt').read_text().startswith('Completed task:')
print('contract demo ok')
PY
