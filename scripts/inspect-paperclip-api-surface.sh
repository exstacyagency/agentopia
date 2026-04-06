#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/work/.openclaw/workspace/upstream-paperclip"
for file in \
  "$ROOT/server/src/routes/index.ts" \
  "$ROOT/server/src/routes/issues.ts" \
  "$ROOT/server/src/routes/approvals.ts" \
  "$ROOT/server/src/routes/goals.ts" \
  "$ROOT/server/src/routes/agents.ts"; do
  echo "===== ${file#$ROOT/} ====="
  sed -n '1,220p' "$file"
  echo
 done
