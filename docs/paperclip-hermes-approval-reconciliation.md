# Paperclip ↔ Hermes Approval Reconciliation

This document describes the lightweight approval reconciliation inspector.

## Script

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/reconcile_approval_status.py
```

## Current reference file

The script compares persisted write-result approval linkage against:
- `var/hermes/approval-status.json`

This file is a lightweight local reference map of:
- approval id → current status

## Output

For recent approval-linked runs, it shows:
- task id
- task type
- approval id
- stored status
- current status
- `status_match`

## Why this exists

Approval linkage is now part of the bridge contract. Reconciliation makes it easier to spot drift between the status captured at execution time and the current approval state known locally.
