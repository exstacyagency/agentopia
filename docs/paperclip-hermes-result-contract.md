# Paperclip ↔ Hermes Result Contract

This document describes the Agentopia-side result contract for Hermes executions triggered from Paperclip.

## Goal

When Paperclip dispatches a Hermes v1 task request, the returned Hermes result envelope should carry enough structured data for downstream consumers to understand:
- what task type ran
- what output was produced
- what artifacts exist
- what execution metadata is attached
- how to trace the result back to Paperclip issue/run context

## Current contract shape

The Hermes executor returns a v1 result envelope with:
- `schema_version`
- `task_id`
- `run`
- `result`
- `artifacts`
- `usage`
- `trace`

## Enriched Agentopia conventions

### `result.summary`
Short human-readable outcome summary.

### `result.output_format`
One of:
- `markdown`
- `json`
- `text`

### `result.output`
Primary content payload for the task.

### `result.notes`
Execution notes describing what happened.

### `result.metadata`
Agentopia convention for structured execution metadata, including:
- `task_type`
- `paperclip_issue_id`
- `paperclip_run_id`
- `paperclip_approval_id`
- `paperclip_approval_status`
- `agent_id`
- task-specific context fields

### `artifacts`
Artifact list for downstream consumers. Even when minimal, the executor should return at least a structured-output artifact entry.

## Why this exists

This keeps the result-side bridge contract explicit in Agentopia, the repo of record, instead of leaving the meaning of executor output implicit.
