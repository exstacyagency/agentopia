# Timeout Enforcement

This document defines the current minimal timeout enforcement baseline for the Paperclip queue.

## Goals

- detect stuck running work
- fail tasks that exceed a configured queue/runtime timeout window
- keep timeout handling persisted and inspectable

## Current model

Queue items now track:

- `started_at`
- `timeout_at`

When a queued task is dispatched, Paperclip records when execution started and when it should be considered timed out.

## Current behavior

If a running queue item passes `timeout_at` before a result is recorded:

- Paperclip marks the queue item as `timed_out`
- Paperclip transitions the task to `failed`
- Paperclip records a timeout audit event

## Current config

- `PAPERCLIP_QUEUE_TIMEOUT_SECONDS`

Default:

- `300` seconds

## Verification

Run:

```bash
./.venv/bin/python scripts/test_timeout_enforcement.py
```

## Notes

This timeout slice does not yet include:

- active worker interruption
- Hermes-side cancellation
- per-task custom timeout classes
- dead-letter routing after timeout
