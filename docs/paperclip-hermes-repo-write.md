# Paperclip ↔ Hermes Repo Write

This document describes the constrained `repo_write` route.

## Intent

`repo_write` is the second narrowly approved write-capable route after `file_write`.

It is intentionally constrained:
- workspace-scoped only
- explicit approval required
- no shell execution

## Modes

### Preview mode
If:
- `apply = false`
- approval is still present
- `changes` is non-empty

then `repo_write` returns a preview result instead of applying writes.

Preview mode includes:
- `policy.mode = preview`
- `policy.reason = repo_write_preview`
- per-file hash and preview metadata
- `repo_write.preview_only = true`

### Apply mode
If:
- `apply = true`
- explicit approval is present
- `changes` is non-empty

then `repo_write` applies workspace-scoped changes.

Apply mode includes:
- `policy.mode = allow`
- `policy.reason = explicit_repo_write_approval`
- `repo_write.preview_only = false`

## Overwrite rule
If any repo-write change sets:
- `overwrite = true`

then that specific change must also set:
- `overwrite_approved = true`

Otherwise the request is policy-blocked with:
- `error.code = POLICY_BLOCKED`
- `policy.reason = repo_write_overwrite_requires_explicit_approval`

## Change shape
Each change entry should include:
- `file_path`
- `content`
- optional `overwrite`
- optional `overwrite_approved`

## Result metadata
`result.metadata.repo_write` includes:
- `preview_only`
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
  - `overwrite_approved`

## Safety model
`repo_write` reuses the same workspace-scoped protections as `file_write`.
Anything outside workspace scope fails with `WRITE_SCOPE_VIOLATION`.
