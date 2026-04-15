# Strict Write Boundaries

This document defines the current write-boundary baseline for Hermes workspace mutations.

## Goals

- prevent file and repo writes from escaping the configured workspace root
- reject path traversal before write helpers run
- make boundary violations explicit and testable

## Current behavior

Hermes now enforces workspace write boundaries for:

- `file_write`
- `file_revert`
- `repo_write`

If a requested path escapes the workspace root:

- Hermes rejects the task
- Hermes returns `WRITE_BOUNDARY_DENIED`
- no write helper runs

## Scope

This slice enforces path-based write boundaries for current workspace mutations.

It does not yet provide:

- OS-level filesystem sandboxing
- mount/jail isolation
- artifact-specific sub-boundaries

## Verification

Run:

```bash
./.venv/bin/python scripts/test_strict_write_boundaries.py
```
