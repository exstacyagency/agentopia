# Hermes Command Runner Boundary

This document defines the current deny-by-default command execution baseline for Hermes.

## Goals

- create a single choke point for command execution
- deny command execution by default
- allow command execution only through an explicit injected runner

## Current model

Hermes now exposes:

- `CommandRunner`
- `DenyByDefaultRunner`
- `SandboxAdapterRunner`

The executor routes `shell_command` tasks through this runner boundary.

## Current behavior

For `shell_command` tasks:

- default behavior is deny
- Hermes returns a sandbox denial error instead of executing the command
- execution only succeeds when a runner is injected explicitly

## Scope

This is a foundation slice.

It does not yet provide:

- OS-level sandboxing
- resource isolation
- write or network controls
- sandboxing for file or repo mutations

## Verification

Run:

```bash
./.venv/bin/python scripts/test_hermes_runner_boundary.py
./.venv/bin/python scripts/test_hermes_executor.py
```
