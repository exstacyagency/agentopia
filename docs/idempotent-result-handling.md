# Idempotent Result Handling

This document defines the current minimal idempotent result handling baseline for Paperclip.

## Goals

- prevent duplicate result callbacks from replaying task completion
- keep result persistence safe when Hermes retries delivery
- make repeated result handling return the original stored task state

## Current model

Paperclip now treats result recording as idempotent per task.

If a result already exists for a task:

- Paperclip returns the existing task
- Paperclip does not reapply state transitions
- Paperclip does not overwrite the stored result

## Current behavior

First result callback:

- task transitions to `succeeded` or `failed`
- Paperclip stores the result payload
- Paperclip records audit and trace events

Repeated result callback for the same task:

- Paperclip returns the existing task response
- no second result write occurs
- no duplicate completion transition is attempted

## Verification

Run:

```bash
./.venv/bin/python scripts/test_idempotent_result_handling.py
```

## Notes

This slice does not yet include:

- payload conflict detection for mismatched duplicate results
- explicit callback dedupe keys beyond task identity
- result replay metrics
