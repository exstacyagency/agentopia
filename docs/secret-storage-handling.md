# Secret Storage and Handling Strategy

This document defines the minimum secret storage and handling strategy for Agentopia in its current scaffold state.

## Goals

- keep real secrets out of tracked repo files
- make secret file locations explicit
- distinguish templates from real secret material
- provide a local verification path for obvious mistakes

## Current strategy

### Tracked files may contain placeholders only

Allowed tracked config:

- `.env.example`
- `config/environments/*.env`

These files should contain placeholders, examples, or non-sensitive sample values only.

### Real secret material must be untracked

Use untracked secret files for real values, for example:

- `config/environments/*.secrets.env`
- `config/environments/*.rendered.env`

These paths are gitignored and should remain untracked.

### Local runtime exception

This scaffold currently tracks `.env` for local defaults.

That file must not be treated as a production secret store.
Production-like real secrets should still live in untracked secret files and rendered deployment env files.

## Minimum handling rules

- do not commit real API keys, bearer tokens, passwords, or production secrets
- keep secret values in untracked files or a secret manager export step
- validate rendered production env files before deployment
- prefer redaction in persisted outputs when secret-bearing values may appear

## Verification

Run:

```bash
./.venv/bin/python scripts/test_secret_handling.py
```

## Definition of done for this item

This repo can consider secret storage and handling minimally defined when:

- secret handling rules are documented
- tracked secret-file patterns remain gitignored
- a local verification path exists for obvious repo-level secret handling mistakes
