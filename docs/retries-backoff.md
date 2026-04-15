# Retries with Backoff

This document defines the current minimal retry and backoff baseline for the Paperclip durable queue.

## Goals

- keep transient dispatch failures from dropping queued work
- persist retry counters and retry timing in the queue
- use a deterministic backoff policy that is easy to inspect

## Current model

Queue items now track:

- `attempt_count`
- `max_attempts`
- `next_attempt_at`
- `last_error`

## Current behavior

When Paperclip tries to dispatch a queued task and Hermes submission fails:

- the task remains queued
- the queue item attempt counter increments
- the queue item records the latest error string
- the queue item schedules the next attempt using backoff

Current backoff policy:

- attempt 1 failure -> retry after 5 seconds
- attempt 2 failure -> retry after 10 seconds
- attempt 3 failure -> retry after 20 seconds

Formula:

- `5 * 2^(attempt_count - 1)` seconds

## Current limits

Default max attempts:

- `3`

Config:

- `PAPERCLIP_QUEUE_MAX_ATTEMPTS`
- `PAPERCLIP_QUEUE_BACKOFF_SECONDS`

## Verification

Run:

```bash
./.venv/bin/python scripts/test_retries_backoff.py
```

## Notes

This slice does not yet include:

- leasing
- jitter
- dead-letter queues
- automatic worker loops
