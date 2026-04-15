# Transactional State Updates

This document defines the current minimal transactional state update baseline for Paperclip.

## Goals

- avoid partial writes when task state and audit/history updates belong together
- make completion recording atomic with its audit side effects
- reduce drift between task state and audit trail during failures

## Current scope

Paperclip now wraps these flows in database transactions:

- task state transition + related audit events
- result storage + result audit event

## Current behavior

If a transaction-scoped operation fails mid-flight:

- partial state/audit writes should not be committed
- Paperclip preserves the last committed state

## Verification

Run:

```bash
./.venv/bin/python scripts/test_transactional_state_updates.py
```

## Notes

This slice improves transactional safety for the existing SQLite path.
It does not yet guarantee full transactional parity for the partial Postgres backend path.
