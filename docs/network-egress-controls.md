# Network Egress Controls

This document defines the current network egress control baseline for Hermes command execution.

## Goals

- reject command execution that implies network access when policy forbids it
- enforce network intent before the command runner executes
- make network-denial behavior explicit and testable

## Current scope

Hermes currently enforces network egress policy for:

- `shell_command` tasks

## Current behavior

Hermes inspects the command string for network-oriented hints such as:

- `curl`
- `wget`
- `http://`
- `https://`
- `nc`
- `ping`

If network intent is detected and `execution_policy.permissions.allow_network` is false:

- Hermes rejects the task
- Hermes returns `NETWORK_EGRESS_DENIED`

## Notes

This slice does not yet provide:

- OS-level network sandboxing
- DNS/socket blocking
- network controls for non-command task types

## Verification

Run:

```bash
./.venv/bin/python scripts/test_network_egress_controls.py
```
