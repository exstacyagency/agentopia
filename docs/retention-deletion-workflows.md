# Retention and Deletion Workflows

This document defines the current minimal retention and deletion baseline for Paperclip task data.

## Goals

- identify completed tasks that are eligible for retention cleanup
- provide a repeatable delete path for task-owned database and filesystem state
- keep deletion scoped to task-owned records and durable storage

## Current retention model

Paperclip can list retention candidates for tasks that are:

- older than a chosen cutoff time
- in a terminal state
  - `succeeded`
  - `failed`
  - `rejected`

## Current deletion behavior

Deleting a task removes:

- task row
- audit events
- queue metadata
- result record
- idempotency mapping
- durable filesystem storage under `var/paperclip/tasks/<task_id>/`

## Current verification

Run:

```bash
./.venv/bin/python scripts/test_retention_deletion_workflows.py
```

## Notes

This slice does not yet include:

- policy-driven automatic deletion schedules
- soft-delete tombstones
- tenant-specific retention policy controls
- artifact-only partial deletion modes
