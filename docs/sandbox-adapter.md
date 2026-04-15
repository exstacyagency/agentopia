# Hermes Sandbox Adapter

This document defines the current OS-level sandbox adapter baseline for Hermes command execution.

## Goals

- provide a real execution adapter beyond deny-by-default policy checks
- run shell commands inside an OS sandbox
- restrict writes to the workspace and block network access by default

## Current implementation

Hermes now includes:

- `MacOSSandboxAdapter`
- `SandboxAdapterRunner`

The adapter uses:

- `sandbox-exec` on macOS

## Current behavior

For `shell_command` tasks executed through the sandbox adapter:

- command execution is isolated by a sandbox profile
- file writes are restricted to:
  - the workspace root
  - a temporary sandbox directory
- network access is denied

## Verification

Run:

```bash
./.venv/bin/python scripts/test_sandbox_adapter.py
```

## Notes

This slice provides real OS-level isolation for the current macOS runtime path.
It does not yet provide:

- Linux container/jail isolation
- Windows sandbox support
- sandboxing for file/repo helper paths that do not execute through the command runner
