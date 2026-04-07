# Paperclip ↔ Hermes Approval Contract

This document describes approval linkage as a first-class part of the Agentopia bridge contract.

## Task request context

Paperclip-originated Hermes task requests may now explicitly carry:
- `paperclip_approval_id`
- `paperclip_approval_status`

These fields travel through the mapped task context and are intended to preserve the Paperclip approval object that authorized risky write-capable work.

## Result metadata

Write-capable Hermes result metadata now surfaces:
- `paperclip_approval_id`
- `paperclip_approval_status`

## Why this matters

This moves approval linkage from an ad hoc context detail to a documented bridge contract element. That improves auditability and makes it easier for operator tooling to distinguish local policy decisions from Paperclip-native approval state.
