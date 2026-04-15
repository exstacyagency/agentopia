# Per-Tool Permission Enforcement

This document defines the current per-tool permission enforcement baseline for Hermes.

## Goals

- map Hermes task types to explicit tool classes
- reject execution when the requested tool class is not allowed by policy
- enforce permissions before execution helpers run

## Current task-to-tool-class mapping

- `repo_summary` -> `repo_read`
- `text_generation` -> `local_exec`
- `file_write` -> `file_write`
- `file_revert` -> `file_write`
- `repo_write` -> `repo_write`
- `shell_command` -> `local_exec`

## Current behavior

Hermes checks `execution_policy.permissions.allowed_tool_classes` before execution.

If the required tool class is absent:

- Hermes rejects the task
- Hermes returns `TOOL_PERMISSION_DENIED`

## Verification

Run:

```bash
./.venv/bin/python scripts/test_tool_permissions.py
```
