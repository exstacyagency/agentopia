# Dangerous Action Tests

This document defines the current dangerous-path test baseline for Hermes mutation and command execution.

## Covered paths

The current focused dangerous-action suite covers denial behavior for:

- `file_write`
- `repo_write`
- `shell_command`

## Verified denial cases

Current tests verify:

- out-of-workspace file writes are denied
- out-of-bounds repo writes are denied
- disallowed shell syntax is denied
- network-intent shell commands are denied when network is disabled
- shell execution without required tool permission is denied

## Verification

Run:

```bash
./.venv/bin/python scripts/test_dangerous_action_coverage.py
```
