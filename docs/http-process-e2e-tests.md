# End-to-End HTTP/Process Tests

This document defines the current end-to-end HTTP/process test baseline.

## Covered flow

The current end-to-end test covers the public Paperclip HTTP control-plane flow:

1. submit a task through `POST /tasks`
2. complete the task through the configured dispatch/service path
3. fetch task status through `GET /tasks/<id>`
4. fetch audit history through `GET /tasks/<id>/audit`
5. list task history through `GET /tasks`

## Scope

This is an in-process end-to-end HTTP/process test for the current public Paperclip flow.
It verifies the customer-visible control-plane path behaves correctly across submit, process, status, audit, and history surfaces.

## Verification

Run:

```bash
./.venv/bin/python scripts/test_http_process_e2e.py
```
