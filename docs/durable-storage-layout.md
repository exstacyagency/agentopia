# Durable Storage Layout for Artifacts and Results

This document defines the current minimal durable storage layout baseline for Agentopia artifacts and results.

## Goals

- give persisted outputs a predictable on-disk layout
- separate task results from task artifacts
- make operator inspection and backup coverage straightforward

## Current layout

Paperclip durable storage root:

- `var/paperclip/tasks/<task_id>/`

Inside each task directory:

- `result.json`
- `artifacts/`

Hermes runtime persistence remains under:

- `var/hermes/`

This slice makes Paperclip’s durable result layout explicit so stored task outputs are not only implicit in the database.

## Current behavior

When Paperclip records a result:

- it stores the result in the database as before
- it writes a durable JSON copy to `var/paperclip/tasks/<task_id>/result.json`
- it ensures `artifacts/` exists for future task-owned files

## Verification

Run:

```bash
./.venv/bin/python scripts/test_durable_storage_layout.py
```

## Notes

This slice does not yet include:

- object storage
- retention/deletion workflows
- artifact metadata indexing in the database
- remote replication
