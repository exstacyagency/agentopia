# Paperclip ↔ Hermes Repo Write

This document describes the initial constrained `repo_write` route.

## Intent

`repo_write` is the second narrowly approved write-capable route after `file_write`.

It is intentionally constrained:
- workspace-scoped only
- explicit approval required
- `apply = true` required
- one or more file changes required
- no shell execution

## Required conditions

`repo_write` is allowed only when:
- `execution_policy.approval.required = true`
- `execution_policy.approval.status = approved`
- `execution_policy.permissions.write_scope = workspace_scoped`
- `task.context.apply = true`
- `task.context.changes` is a non-empty list

## Change shape

Each change entry should include:
- `file_path`
- `content`
- optional `overwrite`

## Result metadata

`result.metadata.repo_write` includes:
- `file_count`
- `files[]` with per-file:
  - `path`
  - `bytes_written`
  - `existed_before`
  - `changed`
  - `previous_bytes`
  - `previous_sha256`
  - `new_sha256`
  - `change_preview`
  - `overwrite`

## Safety model

`repo_write` reuses the same workspace-scoped file protections as `file_write`.
Anything outside workspace scope fails with `WRITE_SCOPE_VIOLATION`.
