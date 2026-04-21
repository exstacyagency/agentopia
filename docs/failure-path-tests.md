# Failure-Path Tests

This document defines the current failure-path test baseline.

## Covered failure paths

The current focused suite covers:

- dispatch failure causing queued retry state with preserved error details
- rejection of cancellation for terminal tasks
- HTTP cancellation of a missing task returning a structured not-found error

## Verification

Run:

```bash
./.venv/bin/python scripts/test_failure_path_coverage.py
```
