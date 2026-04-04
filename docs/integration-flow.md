# Paperclip ↔ Hermes Minimal Integration Flow

This is the first real integration pass between the control plane and execution plane.

## What it does

- Paperclip validates and stores a task
- if approval is not required, Paperclip dispatches the stored request payload to Hermes
- Paperclip moves task state through:
  - `approved -> queued -> running -> succeeded|failed`
- Hermes executes the request and returns a v1 result envelope
- Paperclip stores the result and records audit events

## Current implementation shape

This integration is currently in-process via a dispatch client that calls the Hermes executor directly.

That is intentional for the first pass:
- it proves the shared envelopes work end to end
- it proves task state transitions work
- it proves results can be persisted and audited
- it avoids introducing network transport complexity too early

## What comes next

The next pass should replace the in-process dispatch with real service-to-service transport:
- Paperclip HTTP/internal dispatch client
- Hermes callback or Paperclip result ingest endpoint
- persistent run metadata
- richer audit detail

## Validation

Run:

```bash
PYTHONPATH=. python3 scripts/test_contract_schemas.py
PYTHONPATH=. python3 scripts/test_paperclip_service.py
PYTHONPATH=. python3 scripts/test_hermes_executor.py
PYTHONPATH=. python3 scripts/test_integration_flow.py
```
