# Task Status and History Visibility

This document defines the current customer-facing task status and history visibility baseline.

## Current behavior

Paperclip now supports:

- `GET /tasks`
- `GET /tasks/<id>`
- `GET /tasks/<id>/audit`

## What customers can do

Customers can now:

- list their visible task history with `GET /tasks`
- inspect current task state with `GET /tasks/<id>`
- inspect task audit events with `GET /tasks/<id>/audit`

## Tenant isolation

Task history is tenant-scoped.
A caller only receives tasks for the authenticated tenant.

## Verification

Run:

```bash
./.venv/bin/python scripts/test_task_status_history_visibility.py
```
