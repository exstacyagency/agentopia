#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cat > /tmp/agentopia-request.yml <<'YAML'
task:
  id: task-123
  title: Summarize repo changes
  priority: medium
  requester:
    id: human
    displayName: human
  budget:
    maxCostUsd: 5
    maxRuntimeMinutes: 15
  approval:
    required: false
  constraints:
    outputFormat: markdown
    outputLength: short
    allowNetwork: false
  routing:
    inbound: paperclip
    outbound: hermes
YAML

cat > /tmp/agentopia-result.yml <<'YAML'
result:
  taskId: task-123
  status: success
  summary: "Repository scaffold updated and documented."
  artifacts:
    - README.md
    - docs/example-flow.md
  audit:
    approvedBy: paperclip
    executedBy: hermes
    runtimeSeconds: 12
YAML

for f in /tmp/agentopia-request.yml /tmp/agentopia-result.yml; do
  grep -q '^task:\|^result:' "$f"
done

echo "contract demo ok"
