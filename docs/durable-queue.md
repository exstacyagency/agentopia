# Durable Queue

This document defines the current minimal durable queue baseline for Paperclip.

## Goals

- persist approved work before execution begins
- separate task acceptance from task dispatch
- allow queue inspection without depending on in-memory process state

## Current model

Paperclip now writes approved tasks into a SQLite-backed queue table.

Queue records include:

- `task_id`
- `status`
- `correlation_id`
- `created_at`
- `updated_at`

## Current behavior

When a task is approved:

- Paperclip transitions the task into `queued`
- Paperclip persists a queue record
- Paperclip does not need to rely on in-memory state to remember pending work

A queue processor can then:

- inspect queued work
- dispatch the next queued task to Hermes
- mark the queue item as dispatched

## Current limitations

This queue slice is intentionally minimal. It does not yet include:

- retries with backoff
- timeouts
- worker leasing
- dead-letter handling
- automatic background workers

## Verification

Run:

```bash
./.venv/bin/python scripts/test_durable_queue.py
```
