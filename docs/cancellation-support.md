# Cancellation Support

This document defines the current cancellation baseline for Agentopia.

## Goals

- allow queued and running tasks to be cancelled explicitly
- persist cancellation in task and queue state
- prevent late Hermes results from overwriting a cancelled task
- expose cancellation through the Paperclip HTTP surface

## Current behavior

Paperclip now supports cancellation for tasks in these states:

- `received`
- `validating`
- `pending_approval`
- `approved`
- `queued`
- `running`

Cancellation currently does the following:

- transitions the task to `cancelled`
- marks any queue item as `cancelled`
- records audit events for the cancellation action
- rejects late Hermes result recording for already-cancelled tasks

## Public endpoint

Paperclip supports:

- `POST /tasks/<id>/cancel`

For client-authenticated callers, cancellation is tenant-scoped the same way task reads are.

## Notes

This slice provides durable control-plane cancellation for the current architecture.
It does not yet provide:

- hard process termination inside every possible Hermes runtime
- cooperative mid-tool cancellation hooks inside every Hermes helper
- distributed cancellation propagation beyond the current Paperclip queue/result boundary

## Verification

Run:

```bash
./.venv/bin/python scripts/test_cancellation_support.py
```
