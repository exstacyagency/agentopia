# Paperclip ↔ Hermes Run Inspector

This document describes the lightweight local inspection scripts for recent Hermes runs and accepted callback results.

## Scripts

### Recent persisted runs
```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_recent_runs.py
```

Shows up to 20 recent persisted Hermes run records with:
- task id
- run id
- status
- summary
- task type
- trace id

### Recent callback results
```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_callback_results.py
```

Shows up to 20 accepted callback payloads with:
- task id
- run id
- status
- summary
- task type
- stored timestamp

## Why this exists

The bridge now produces durable state. These scripts provide a simple operator view without manually opening raw JSON files under `var/hermes/`.
