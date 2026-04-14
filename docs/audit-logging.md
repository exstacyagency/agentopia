# Audit Logging

This document defines the minimum audit logging baseline for Agentopia in its current scaffold state.

## Goals

- preserve an internal record of important control-plane and execution-plane events
- make audit writes explicit and queryable
- keep the baseline lightweight but durable

## Current baseline

Audit logging should capture important Paperclip and Hermes events to internal repo-controlled storage.

### Paperclip
Paperclip already stores audit events in SQLite.

Minimum expectation:

- task lifecycle events remain persisted
- audit events remain queryable via the service layer

### Hermes
Hermes should record important persistence-side events to an internal audit log file.

Minimum expectation:

- persisted result writes are recorded
- callback recording attempts are recorded
- audit records are written in structured JSON lines format

## Current storage

- Paperclip audit events: SQLite
- Hermes audit events: `var/hermes/audit.log`

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_audit_logging.py
```

## Definition of done for this item

This repo can consider audit logging minimally defined when:

- Paperclip audit persistence remains in place
- Hermes writes structured audit records for key persistence events
- audit behavior is documented and tested
