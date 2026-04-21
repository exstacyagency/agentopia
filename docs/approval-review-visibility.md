# Approval and Review Visibility

This document defines the current customer-facing approval/review visibility baseline.

## Current behavior

Task detail responses now include:

- `approval_review`

This summary gives customers a compact view of whether a task is awaiting approval or has already been reviewed.

## Current fields

- `approval_status`
- `current_state`
- `review_required`
- `latest_review_event`

## Why this helps

Customers can now tell, from the normal task response:

- whether approval is still pending
- whether review action is required
- what the latest approval/review event was

without manually reconstructing that state from the full audit log.

## Verification

Run:

```bash
./.venv/bin/python scripts/test_approval_review_visibility.py
```
