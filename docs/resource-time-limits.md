# Resource and Time Limits

This document defines the current execution limit baseline for Hermes.

## Goals

- enforce runtime caps across Hermes execution paths, not just the shell runner
- fail execution that exceeds the allowed runtime budget
- limit oversized Hermes execution outputs before they become durable results
- keep time and size limit failures explicit and testable

## Current scope

Hermes currently enforces execution limits for:

- `shell_command` tasks executed through the command runner boundary
- non-runner Hermes task handlers at the executor boundary
- oversized Hermes execution payloads before success results are returned

## Current behavior

Hermes converts `execution_policy.budget.max_runtime_minutes` into an execution runtime limit.

This limit now applies at two layers:

- runner-level runtime enforcement for `shell_command`
- executor-level runtime enforcement around Hermes task handlers

Hermes also supports an execution output size limit using:

- `execution_policy.budget.max_output_bytes`

If runtime or output limits are exceeded:

- Hermes rejects the task result
- Hermes returns `EXECUTION_LIMIT_EXCEEDED`

## Notes

This slice improves execution limits materially, but it still does not provide:

- OS-level CPU quotas
- OS-level memory quotas
- real cancellation/termination of already-running helper logic
- full container or cgroup enforcement across all runtimes

## Verification

Run:

```bash
./.venv/bin/python scripts/test_execution_limits.py
```
