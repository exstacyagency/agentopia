#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/work/.openclaw/workspace/upstream-paperclip/server/src/routes"
check() {
  local file="$1"
  local pattern="$2"
  if grep -q "$pattern" "$file"; then
    echo "PASS: $(basename "$file") contains pattern: $pattern"
  else
    echo "FAIL: $(basename "$file") missing pattern: $pattern" >&2
    exit 1
  fi
}
check "$ROOT/index.ts" "issueRoutes"
check "$ROOT/index.ts" "approvalRoutes"
check "$ROOT/index.ts" "agentRoutes"
check "$ROOT/approvals.ts" "companies/:companyId/approvals"
check "$ROOT/approvals.ts" "approvals/:id/issues"
check "$ROOT/agents.ts" "companies/:companyId/heartbeat-runs"
check "$ROOT/agents.ts" "heartbeat-runs/:runId"
check "$ROOT/agents.ts" "issues/:issueId/active-run"
check "$ROOT/goals.ts" "companies/:companyId/goals"
echo "Step 1 verification complete."
