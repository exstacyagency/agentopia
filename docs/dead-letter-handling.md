# Dead-Letter Handling

This document defines the current minimal dead-letter handling baseline for the Paperclip queue.

## Goals

- stop endlessly retrying permanently failing work
- preserve failed queue records for inspection
- keep dead-letter transitions explicit and audited

## Current model

Queue items now move to a dead-letter state when retry attempts exceed the configured maximum.

Dead-letter items retain:

- `attempt_count`
- `last_error`
- queue metadata for operator inspection

## Current behavior

If queue dispatch keeps failing and the next retry would exceed `max_attempts`:

- the queue item is marked `dead_letter`
- the task is marked `failed`
- Paperclip records a dead-letter audit event
- queue processing stops retrying that item

## Verification

Run:

```bash
./.venv/bin/python scripts/test_dead_letter_handling.py
```

## Notes

This slice does not yet include:

- dedicated dead-letter requeue tooling
- dead-letter dashboards
- automatic notification hooks
