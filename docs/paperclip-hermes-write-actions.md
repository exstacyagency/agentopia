# Paperclip ↔ Hermes Write Action Summary

This document describes the operator-facing summary script for write-capable actions.

## Script

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_write_actions.py
```

## What it shows

For recent persisted write-capable runs (`file_write`, `repo_write`), it shows:
- task id
- run id
- run status
- task type
- policy mode
- policy reason
- summary
- trace id
- write metadata
- error metadata when present

## Why this exists

The bridge is now capable of real approved writes. This script gives operators a quick way to inspect recent write actions, preview states, blocked approvals, and applied write metadata without digging through raw result envelopes manually.
