# Safer Shell Execution Layer

This document defines the current safer shell execution baseline for Hermes `shell_command` tasks.

## Goals

- reject obviously unsafe shell syntax before command execution
- prevent shell-command chaining and redirection constructs
- restrict execution to a small allowlist of lower-risk executables
- keep deny-by-default runner behavior when no explicit runner is configured

## Current behavior

Before Hermes passes a shell command to the runner, it now validates the command through `hermes/shell_safety.py`.

The shell-safety layer rejects:

- chaining and control operators such as:
  - `;`
  - `&&`
  - `||`
  - `|`
  - redirection operators like `>` and `<`
- shell substitution syntax such as:
  - backticks
  - `$()`
- disallowed executables such as:
  - `bash`
  - `sh`
  - `python3`
  - `node`
  - `sudo`
  - `osascript`
- executables that are not on the current allowlist

The current allowlist includes:

- `pwd`
- `ls`
- `cat`
- `echo`
- `git`
- `grep`
- `sed`
- `awk`
- `head`
- `tail`
- `wc`
- `stat`

## Error behavior

Commands rejected by the shell-safety layer return a structured Hermes failure with:

- error code: `SHELL_SAFETY_DENIED`

## Verification

Run:

```bash
./.venv/bin/python scripts/test_shell_safety.py
```

## Scope

This slice hardens the Hermes `shell_command` entry point before runner execution.
It works together with:

- deny-by-default runner behavior
- sandbox adapter execution
- network egress policy checks
- runtime limits

## Notes

This is a pragmatic safety layer for the current command-execution path.
It does not yet provide:

- argument-level semantic allowlists per executable
- cancellation support
- OS-level resource quotas beyond the current runner/runtime path
