# Paperclip ↔ Hermes Approval Linkage

This document describes how Paperclip approval identifiers are surfaced through the Agentopia write workflow.

## Current linkage

Write-capable result metadata now carries:
- `paperclip_approval_id`
- `paperclip_approval_status`

These fields are intended to connect local policy decisions and write-action summaries back to the Paperclip approval object that authorized the work.

## Current operator surface

`python3 scripts/list_write_actions.py` now includes:
- `paperclip_approval.id`
- `paperclip_approval.status`

## Why this matters

The execution plane is already hardened locally. Approval linkage makes the write workflow more auditable by tying approved or blocked actions back to Paperclip-native approval context.
