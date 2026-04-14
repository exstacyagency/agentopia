# Approval Expiration and Timeout Behavior

This document defines the minimum approval expiration baseline for Agentopia in its current scaffold state.

## Goals

- avoid approvals remaining pending forever without review
- make stale approval windows detectable
- keep timeout behavior explicit and testable

## Current baseline

Paperclip should support an approval expiration window for tasks in `pending_approval`.

Default config:

- `PAPERCLIP_APPROVAL_TTL_SECONDS` default `3600`

## Expected behavior

For tasks in `pending_approval`:

- if current time is beyond `updated_at + TTL`, mark the approval as expired
- expired approvals should be surfaced through a helper command
- expired approvals should not silently continue as valid pending approvals

## Current helper

Use:

```bash
./.venv/bin/python scripts/check_approval_expiration.py
```

This reports pending-approval tasks that have exceeded the configured TTL.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_approval_expiration.py
```

## Definition of done for this item

This repo can consider approval expiration minimally defined when:

- expiration rules are documented
- stale pending approvals can be detected through a concrete helper
- behavior is covered by tests
