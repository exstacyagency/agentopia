# Resource and Time Limits

This document defines the current execution limit baseline for Hermes.

## Goals

- enforce runtime caps at the current execution boundary
- fail command execution that exceeds the allowed runtime budget
- make time-limit failures explicit and testable

## Current scope

Hermes currently enforces runtime limits for:

- `shell_command` tasks executed through the command runner boundary

## Current behavior

Hermes converts `execution_policy.budget.max_runtime_minutes` into a runner runtime limit.

If a command runner exceeds that limit:

- Hermes rejects the task result
- Hermes returns `EXECUTION_LIMIT_EXCEEDED`

## Notes

This slice does not yet provide:

- OS-level CPU or memory cgroups/rlimits
- subprocess kill/termination logic in a real sandbox adapter
- runtime enforcement for file or repo helper operations

## Verification

Run:

```bash
./.venv/bin/python scripts/test_execution_limits.py
```
