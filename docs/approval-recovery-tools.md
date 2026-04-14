# Operator Recovery Tools for Stuck Approval States

This document defines the minimum operator recovery baseline for stuck approval states in Agentopia.

## Goals

- give operators a concrete way to find stuck approval tasks
- provide a narrow, auditable recovery action
- avoid direct ad hoc database edits for common stuck-state cases

## Current baseline

Paperclip should support a helper that:

- lists tasks with approval-state mismatches
- lists expired pending approvals
- optionally applies a narrow recovery action to reset a stuck task back to `pending_approval`

## Current helper

Use:

```bash
./.venv/bin/python scripts/recover_stuck_approvals.py --list
./.venv/bin/python scripts/recover_stuck_approvals.py --task-id <id> --reset-pending
```

## Recovery rule

Current supported recovery action:

- reset a task to `pending_approval` with approval status `pending`

This is intentionally narrow. It gives operators one safe recovery path without pretending to solve every governance case automatically.

## Expected behavior

Recovery actions should:

- update task state and approval status together
- emit an audit event
- require an explicit task id

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_approval_recovery.py
```

## Definition of done for this item

This repo can consider operator recovery tools minimally defined when:

- stuck approval tasks can be listed through a helper
- a narrow recovery action exists
- recovery behavior is documented and tested
