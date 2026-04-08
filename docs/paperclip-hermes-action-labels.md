# Paperclip ↔ Hermes Action Labels

This document describes the semantic labeling layer for Paperclip-driven actions.

## New metadata fields

Recent Hermes result metadata may now include:
- `action_label`
- `action_category`
- `action_reason`
- `operator_summary`
- `issue_origin`

## Why this exists

Operators need more than raw execution metadata. These fields explain:
- what kind of action was produced
- why it was produced
- how to read it quickly

## Example categories
- `analysis`
- `planning`
- `drafting`
- `preview_write`
- `approved_write`
- `blocked_write`
- `general`

## Current summary surface

`python3 scripts/list_write_actions.py` now includes the action-label fields for recent write-capable runs.
