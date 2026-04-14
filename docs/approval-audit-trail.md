# Approval Action Audit Trail

This document defines the minimum audit trail baseline for approval actions in Agentopia.

## Goals

- make approval-related actions explicitly auditable
- distinguish approval decisions from general task lifecycle events
- give operators a direct way to inspect approval history

## Current baseline

Paperclip should emit dedicated audit events for approval actions.

Minimum approval action events:

- `approval_requested`
- `approval_granted`
- `approval_rejected`
- `approval_expired`

## Current helper

Use:

```bash
./.venv/bin/python scripts/list_approval_audit_events.py <task_id>
```

This prints approval-specific audit events for the given task.

## Expected behavior

Approval action events should include:

- task id
- actor
- event type
- timestamp
- any relevant decision details

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_approval_audit_trail.py
```

## Definition of done for this item

This repo can consider approval action audit trail minimally defined when:

- approval-specific audit events are emitted
- approval audit events can be queried separately from generic task audit history
- behavior is documented and tested
