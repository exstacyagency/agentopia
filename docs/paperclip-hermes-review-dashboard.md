# Paperclip ↔ Hermes Review Dashboard

This document describes the unified operator review script for write-capable actions.

## Script

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/review_write_actions.py
```

## What it groups

The script groups recent write-capable runs into:
- `pending_previews`
- `blocked_actions`
- `applied_writes`
- `approval_mismatches`

## Per-entry fields

Entries include:
- task id
- run id
- task type
- operator status
- action label/category
- operator summary
- action reason
- policy mode / reason
- Paperclip issue id
- Paperclip approval id / stored status
- current approval status when locally known
- approval drift flag
- error details when present

## Why this exists

This is the first review/dashboard layer for approving, understanding, and auditing risky write-capable actions before a future rollback workflow is added.
