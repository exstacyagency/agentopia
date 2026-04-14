# Tracing and Request/Run Visibility

This document defines the minimum tracing-equivalent visibility baseline for Agentopia in its current scaffold state.

## Goals

- make request and run flow visible without a full tracing backend
- preserve a local trail from Paperclip intake through Hermes execution result persistence
- give operators a single place to inspect recent trace records

## Current baseline

Agentopia should persist lightweight JSON trace records for important flow events.

Minimum covered events:

- Paperclip task submission
- Paperclip dispatch to Hermes
- Hermes execution receipt
- Hermes result persistence
- Paperclip result recording

## Current storage

Trace records should be written to:

- `var/traces/trace-<id>.jsonl`

Each line is a JSON object with:

- `timestamp`
- `trace_id`
- `service`
- `event`
- optional structured fields

## Current scope

This is not full distributed tracing.
It is a local trace log for request/run visibility using the trace and correlation IDs already present in the repo.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_tracing_visibility.py
```

## Definition of done for this item

This repo can consider tracing/request-run visibility minimally defined when:

- important flow events are appended to per-trace logs
- the trace log path is documented
- behavior is covered by tests
