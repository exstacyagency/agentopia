# Paperclip ↔ Hermes Issue Actions

This document describes the first backend command contract for native Paperclip issue-level controls.

## Endpoint

```bash
POST /internal/issue-action
```

## Current actions

### `resolve_revert_candidates`
Returns recent successful `file_write` runs for the given issue along with revert payload candidates.

### `apply_preview`
Accepts an issue-scoped action envelope and returns a contract-ready response for future execution wiring.

### `file_revert`
Accepts an issue-scoped action envelope and returns a contract-ready response for future execution wiring.

## Example payload

```json
{
  "issue_id": "paperclip-issue-id",
  "action": "file_revert",
  "context": {
    "source_run_id": "run_123",
    "file_path": "tmp/example.txt"
  }
}
```

## Why this exists

This gives the native Paperclip review panel a truthful backend contract to call before execution buttons are fully wired to concrete Hermes execution paths.

The `resolve_revert_candidates` action is the missing target-resolution step needed before a real Revert button can safely execute.

## Current status

This is a real backend action surface, but it is still a contract layer:
- action acceptance works
- response shape is stable enough for UI integration
- concrete execution attachment is the next step
