# Consistent Error Messages

This document defines the current customer-facing API error baseline.

## Current behavior

Paperclip public API errors now use a consistent JSON shape:

```json
{
  "error": {
    "code": "task_not_found",
    "message": "Task not found",
    "status": 404,
    "details": {}
  }
}
```

## Goals

- keep error payloads structurally consistent
- give customers a stable machine-readable code
- keep human-readable messages straightforward
- include optional details only when useful

## Current coverage

This shape now covers the main public API error paths, including:

- unauthorized
- forbidden
- not found
- invalid request
- request too large
- rate limit exceeded

## Verification

Run:

```bash
./.venv/bin/python scripts/test_consistent_error_messages.py
```
