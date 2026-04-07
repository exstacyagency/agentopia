# Paperclip ↔ Hermes Policy Gating

This document describes the current policy gate for Hermes task execution.

## Current policy mode

Default behavior:
- allow known read-only and planning routes
- deny write-capable routes unless explicit policy support is added

## Allowed task types
- `repo_summary`
- `file_analysis`
- `text_generation`
- `structured_extract`
- `repo_change_plan`
- `implementation_draft`

## Explicitly approved write path

### `file_write`
`file_write` is allowed only when all of the following are true:
- `execution_policy.approval.required = true`
- `execution_policy.approval.status = approved`
- `execution_policy.permissions.write_scope = workspace_scoped`
- `task.context.file_path` is present

When allowed, result metadata includes:
- `policy.mode = allow`
- `policy.reason = explicit_file_write_approval`

## Still blocked task types
- `repo_write`
- `shell_command`
- `file_write` without the explicit approval conditions above

Blocked write-capable routes return a failed result with:
- `error.code = POLICY_BLOCKED`
- `result.metadata.policy.mode = deny`
- `result.metadata.policy.reason = write_capable_requires_explicit_policy`

## Why this exists

The bridge is live, durable, callback-capable, and inspectable. The next safe step is to introduce one narrow approved write path without losing deny-by-default protection for broader write execution.
