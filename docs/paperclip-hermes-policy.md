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

When allowed, Hermes performs a real workspace-scoped file write.

Result metadata includes:
- `policy.mode = allow`
- `policy.reason = explicit_file_write_approval`
- `file_write.path`
- `file_write.bytes_written`
- `file_write.existed_before`
- `file_write.changed`
- `file_write.previous_bytes`
- `file_write.overwrite`

Result artifacts include a `file_write` artifact pointing at the written workspace-relative path.

## Overwrite behavior

`file_write` defaults to `overwrite = false`.

That means:
- creating a new file is allowed
- rewriting the same content is allowed and reports `changed = false`
- changing an existing file without `overwrite = true` is rejected

Overwrite rejections return:
- `error.code = WRITE_SCOPE_VIOLATION`
- `error.message = target file exists and overwrite is false`

## Still blocked task types
- `repo_write`
- `shell_command`
- `file_write` without the explicit approval conditions above

Blocked write-capable routes return a failed result with:
- `error.code = POLICY_BLOCKED`
- `result.metadata.policy.mode = deny`
- `result.metadata.policy.reason = write_capable_requires_explicit_policy`

## Scope guardrails

`file_write` is restricted to workspace-scoped paths only.

It rejects:
- empty target paths
- paths that resolve outside the Agentopia workspace
- path traversal attempts

These failures return `error.code = WRITE_SCOPE_VIOLATION`.

## Why this exists

The bridge is live, durable, callback-capable, and inspectable. The next safe step is to introduce one narrow approved write path without losing deny-by-default protection for broader write execution.
