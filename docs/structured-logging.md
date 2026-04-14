# Structured Logging

This document defines the minimum structured logging baseline for Agentopia in its current scaffold state.

## Goals

- emit machine-readable service logs
- make request and lifecycle events easier to inspect
- keep logs consistent between Paperclip and Hermes

## Current baseline

Paperclip and Hermes should emit JSON log lines for key service events.

Minimum event types:

- service start
- incoming request
- handled response
- rejected request where applicable

## Current format

Each log line should include:

- `timestamp`
- `service`
- `event`
- optional structured fields relevant to the event

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_structured_logging.py
```

## Definition of done for this item

This repo can consider structured logging minimally defined when:

- both services emit JSON log lines
- log entries include a stable service name and event type
- logging behavior is documented and tested
