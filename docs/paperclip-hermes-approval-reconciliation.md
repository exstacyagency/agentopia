# Paperclip ↔ Hermes Approval Reconciliation

This document describes the approval reconciliation inspector.

## Script

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/reconcile_approval_status.py
```

## Live lookup mode

If `PAPERCLIP_COMPANY_ID` is set, the script first attempts to fetch current approval state from Paperclip using:
- `PAPERCLIP_BASE_URL` (default `http://127.0.0.1:3100`)
- `PAPERCLIP_COMPANY_ID`

In that mode, output includes:
- `status_source = paperclip_live`

## Local fallback mode

If live lookup is unavailable or fails, the script falls back to:
- `var/hermes/approval-status.json`

In that mode, output includes:
- `status_source = local_fallback`

## Output

For recent approval-linked runs, it shows:
- task id
- task type
- approval id
- stored status
- current status
- `status_source`
- `status_match`

## Why this exists

Approval linkage is now part of the bridge contract. Reconciliation makes it easier to spot drift between the status captured at execution time and the current approval state, with live Paperclip lookup preferred when available.
