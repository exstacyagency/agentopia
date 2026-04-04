# Paperclip Minimal Intake API

This is the first real implementation step beyond the contract docs.

## Scope

The Paperclip minimal API currently provides:

- `POST /tasks` — validate and persist a task request
- `GET /tasks/:id` — fetch persisted task metadata
- `POST /tasks/:id/approve` — approve a pending task
- `POST /tasks/:id/reject` — reject a pending task
- `GET /tasks/:id/audit` — fetch audit events
- `GET /health` — health check

## Current behavior

- request payloads are validated against `schemas/task_request_v1.json`
- accepted tasks are stored in SQLite
- task lifecycle state is enforced via a state machine
- audit events are written for receipt and transitions

## Current limitations

- no Hermes dispatch yet
- no result ingestion endpoint yet
- no budget accounting beyond accepted payload values
- no auth layer yet
- uses the standard library HTTP server for a minimal local implementation

## Run locally

```bash
PYTHONPATH=. python3 paperclip/app.py
```

Then submit a task with a valid request fixture.

## Why this exists

This is the narrowest useful slice of a real Paperclip implementation:
- intake
- validation
- persistence
- state management
- audit trail

That gives Hermes something real to integrate with next.
