# Paperclip ↔ Hermes Rollback

This document describes the first constrained rollback path implemented in Agentopia.

## Scope

Initial rollback support is intentionally narrow:
- task type: `file_revert`
- workspace-scoped only
- explicit approval required
- prior content must be supplied explicitly in task context

This is an Agentopia-first rollback primitive. It does not attempt a universal automatic undo system.

## Policy requirements

`file_revert` is allowed only when:
- approval is required
- approval status is `approved`
- `write_scope = workspace_scoped`
- `file_path` is present
- `previous_content` is present

Otherwise the task is blocked with:
- `policy.reason = file_revert_requires_explicit_approval`

## Context shape

```json
{
  "file_path": "tmp/example.txt",
  "previous_content": "old content\n",
  "source_run_id": "run_prior_write"
}
```

## Result metadata

Successful `file_revert` results include:
- `path`
- `reverted`
- `target_existed_before`
- `restored_bytes`
- `restored_sha256`
- `previous_sha256`
- `change_preview`
- `source_run_id`

## Why this shape

This keeps rollback safe and explicit:
- no shell execution
- no broad repo undo yet
- no hidden lookup magic required for the first version
- operator approval remains mandatory

## Next validation step

After restarting the Hermes executor to load the new route:
1. run a real `file_write`
2. run a real approved `file_revert` against the same file
3. confirm the file content is restored
4. confirm revert metadata is persisted
5. optionally surface revert summaries into Paperclip comments next
