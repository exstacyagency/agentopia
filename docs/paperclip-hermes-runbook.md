# Paperclip ↔ Hermes Local Operator Runbook

This runbook is the canonical Agentopia-side workflow for bringing up the local Paperclip ↔ Hermes bridge and validating that it works end to end.

## Scope

This assumes:
- Agentopia is the repo of record
- Paperclip is a **local-only patched dependency**
- local Paperclip runs separately from Agentopia GitHub workflows

## Services and ports

### Paperclip
- local API/UI: `http://127.0.0.1:3100`
- embedded Postgres: `54329`

### Isolated Hermes gateway
- health/models API: `http://127.0.0.1:8742`

### Agentopia Hermes executor
- health: `http://127.0.0.1:3200/health`
- execute: `http://127.0.0.1:3200/internal/execute`

## Start order

### 1. Start isolated Hermes gateway
```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
API_SERVER_KEY=agentopia-local-dev-key ./scripts/hermes-agentopia-start.sh
```

### 2. Start Agentopia Hermes executor
```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
PYTHONPATH=/Users/work/.openclaw/workspace/repo-agentopia ./.venv/bin/python hermes/app.py
```

### 3. Start local Paperclip
```bash
cd /Users/work/.openclaw/workspace/upstream-paperclip
pnpm --filter @paperclipai/server dev
```

## Readiness checks

### Hermes gateway
```bash
curl http://127.0.0.1:8742/health
```

### Agentopia executor
```bash
curl http://127.0.0.1:3200/health
```

### Paperclip
```bash
curl http://127.0.0.1:3100/api/health
```

### Optional helper checks
```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
./scripts/check-local-paperclip-patch-state.sh
./scripts/check-paperclip-live-ready.sh http://127.0.0.1:3100
```

## Canonical live validations

### Validation A: file_analysis route
Create a file-oriented issue like:
- title: `Analyze docs/README.md for missing setup guidance`
- description: `Please inspect docs/README.md and explain what setup guidance is missing or unclear.`

Success criteria:
- heartbeat run succeeds
- dispatched task type is `file_analysis`
- stored metadata includes `task_type=file_analysis`

### Validation B: text_generation route
Create a drafting-oriented issue like:
- title: `Draft a short release announcement for the Hermes bridge`
- description: `Write a concise announcement for the new Paperclip to Hermes execution bridge.`

Success criteria:
- heartbeat run succeeds
- dispatched task type is `text_generation`
- stored metadata includes `task_type=text_generation`

## Common failure modes

### Paperclip health is up, but requests fail later
Likely cause:
- embedded Postgres on `54329` died

Symptoms:
- `ECONNREFUSED 127.0.0.1:54329`
- scheduler / heartbeat / routine errors in Paperclip logs

Fix:
- restart local Paperclip cleanly

### Hermes executor returns older result shape
Likely cause:
- executor was not restarted after code changes

Fix:
- restart `hermes/app.py` from the repo-local venv

### Paperclip routes everything to repo_summary
Likely cause:
- local Paperclip wakeup context propagation patch missing
- or local Hermes adapter patch drift

Fix:
- verify local-only Paperclip patches are still present

### Hermes gateway fails auth/model calls
Likely cause:
- missing or wrong `API_SERVER_KEY`

Fix:
- restart isolated Hermes with the expected local key

## Source-of-truth docs

- `docs/paperclip-hermes-handoff.md`
- `docs/paperclip-task-mapping-contract.md`
- `docs/paperclip-hermes-result-contract.md`
- `docs/agentopia-local-stack.md`
- `docs/paperclip-upstream-dependency.md`

## Why this runbook exists

The bridge is now functional across multiple mapped task types. This runbook turns that into a reproducible operator workflow instead of relying on chat history or ad hoc memory.
