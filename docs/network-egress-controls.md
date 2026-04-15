# Network Egress Controls

This document defines the current network egress control baseline for Hermes command execution.

## Goals

- reject command execution that implies network access when policy forbids it
- enforce network controls before and during command execution
- connect policy decisions to the OS sandbox path where available
- make network-denial behavior explicit and testable

## Current scope

Hermes currently enforces network egress controls for:

- `shell_command` tasks
- macOS sandbox-adapter command execution

## Current behavior

Hermes now applies network egress control at two layers:

1. policy-level command inspection for `shell_command`
2. OS-level sandbox profile network rules for the macOS sandbox adapter

Policy inspection still detects network-oriented commands such as:

- `curl`
- `wget`
- `http://`
- `https://`
- `nc`
- `ping`

If network intent is detected and `execution_policy.permissions.allow_network` is false:

- Hermes rejects the task
- Hermes returns `NETWORK_EGRESS_DENIED`

For the macOS sandbox adapter:

- network is denied by default in the sandbox profile
- network can be explicitly allowed only when the execution policy allows it

## Notes

This slice materially improves network egress control for the current command-execution path, but it still does not provide:

- non-macOS OS-level network sandboxing
- deep DNS/socket policy controls for all runtimes
- network controls for non-command task types

## Verification

Run:

```bash
./.venv/bin/python scripts/test_network_egress_controls.py
```
