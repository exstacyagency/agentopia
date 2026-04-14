# Approval Reconciliation

This document defines the minimum approval reconciliation baseline for Agentopia in its current scaffold state.

## Goals

- keep approval state transitions explicit and auditable
- provide a way to detect tasks stuck in approval-related states
- make reconciliation possible without manual database guessing

## Current baseline

Paperclip should support a simple reconciliation report for approval-related task states.

Minimum states to reconcile:

- `pending_approval`
- `approved`
- `rejected`

## Current reconciliation checks

Flag tasks that look inconsistent, such as:

- task state is `pending_approval` but approval status is not `pending`
- task state is `approved` but approval status is not `approved` or `not_required`
- task state is `rejected` but approval status is not `rejected`

## Current helper

Use:

```bash
./.venv/bin/python scripts/reconcile_approval_status.py
```

This reports tasks with mismatched task state vs approval status.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_approval_reconciliation.py
```

## Definition of done for this item

This repo can consider approval reconciliation minimally defined when:

- approval/task mismatches can be detected through a concrete helper
- reconciliation rules are documented
- behavior is covered by tests
