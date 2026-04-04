# Hermes Minimal Executor API

This is the first real Hermes implementation slice.

## Scope

The Hermes minimal executor currently provides:

- `POST /internal/execute` — validate and execute a v1 task request
- `GET /health` — health check

## Current behavior

- validates request payloads against `schemas/task_request_v1.json`
- supports one narrow task type: `repo_summary`
- returns a v1 result envelope that validates against `schemas/task_result_v1.json`
- returns structured failures for invalid requests and unsupported task types

## Current limitations

- no callback to Paperclip yet
- no persistence yet
- no tool execution yet
- no memory integration yet
- no real model/provider runtime yet

## Run locally

```bash
PYTHONPATH=. python3 hermes/app.py
```

Then post a valid task request fixture to `/internal/execute`.

## Why this exists

This gives Agentopia its first real execution-plane slice:
- request validation
- narrow task execution
- result generation
- error normalization

That is enough to wire Paperclip → Hermes next.
