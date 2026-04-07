# Paperclip ↔ Hermes Policy Gating

This document describes the initial policy gate for Hermes task execution.

## Current policy mode

Default behavior:
- allow known read-only and planning routes
- deny write-capable routes unless explicit policy support is added later

## Allowed task types
- `repo_summary`
- `file_analysis`
- `text_generation`
- `structured_extract`
- `repo_change_plan`
- `implementation_draft`

## Blocked task types
- `repo_write`
- `file_write`
- `shell_command`

Blocked write-capable routes return a failed result with:
- `error.code = POLICY_BLOCKED`
- `result.metadata.policy.mode = deny`
- `result.metadata.policy.reason = write_capable_requires_explicit_policy`

## Why this exists

The bridge is now live, durable, and inspectable. The next safe extension step is to add explicit control before allowing write-oriented execution.
