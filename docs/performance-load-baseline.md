# Performance and Load Baseline

This document defines the current broader performance/load baseline for Agentopia.

## Goal

Provide a reproducible, scriptable baseline for driving the public Paperclip control-plane flow under concurrent request load.

## Current baseline

The current load baseline uses:

- `scripts/load_test_paperclip.py`

It drives the public API through:

- `POST /tasks`
- task completion through the configured process path
- `GET /tasks/<id>` polling until terminal state

## Example run

```bash
./.venv/bin/python scripts/load_test_paperclip.py \
  --base-url http://127.0.0.1:3100 \
  --api-key tenant-a-key \
  --requests 10 \
  --concurrency 2 \
  --timeout-seconds 15
```

## Output

The script emits a JSON summary containing:

- request count
- concurrency
- ok/error counts
- total runtime
- throughput estimate
- latency min/p50/max
- per-request outcomes

## Current scope

This is a lightweight reproducible baseline for the current public control-plane path.
It does not yet replace:

- deeper soak testing
- distributed load generation
- long-duration resource profiling
- multi-service/container-scale benchmarking

## Verification

Run:

```bash
./.venv/bin/python scripts/test_load_test_paperclip.py
```
