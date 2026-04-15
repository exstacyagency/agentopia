# Hermes Executor Dispatch Boundary

This document defines the current executor refactor baseline for Hermes.

## Goals

- isolate task-type routing behind a single dispatch map
- preserve the existing v1 result envelope while simplifying future executor changes
- prepare Hermes for later sandbox enforcement without changing current file/repo behavior yet

## Current model

Hermes executor now routes supported task types through an internal dispatch boundary.

Current handlers:

- `repo_summary`
- `text_generation`
- `file_write`
- `repo_write`
- `file_revert`

## Current behavior

This refactor is intended to preserve behavior, not change policy.

It does:

- centralize routing in one place
- keep the v1 result envelope explicit
- make future execution boundaries easier to insert

It does not yet do:

- sandbox command execution
- change file or repo mutation permissions
- add OS-level isolation

## Verification

Run:

```bash
./.venv/bin/python scripts/test_hermes_dispatch_boundary.py
./.venv/bin/python scripts/test_hermes_executor.py
```
