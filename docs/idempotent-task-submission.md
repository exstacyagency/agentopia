# Idempotent Task Submission

This document defines the current minimal idempotent task submission baseline for Paperclip.

## Goals

- prevent duplicate task creation from repeated client submits
- make retries safe at the API boundary
- persist idempotency tracking in the Paperclip database

## Current model

Paperclip now supports an idempotency key on task submission.

Header:

- `Idempotency-Key`

Paperclip stores the first submitted task id for a given idempotency key and returns the existing task on later matching requests.

## Current behavior

If a client submits `POST /tasks` with a new idempotency key:

- Paperclip creates the task normally
- Paperclip stores the idempotency mapping

If a client submits again with the same idempotency key:

- Paperclip returns the original task
- Paperclip does not create a second task
- Paperclip does not enqueue duplicate work

## Scope

This baseline is currently keyed only by the provided idempotency key string.

## Verification

Run:

```bash
./.venv/bin/python scripts/test_idempotent_task_submission.py
```

## Notes

This slice does not yet include:

- payload hash conflict detection for reused keys
- expiry/retention rules for idempotency records
- idempotent result handling
