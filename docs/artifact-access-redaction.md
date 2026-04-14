# Artifact Access Controls and Sensitive Output Redaction

This document defines the minimum artifact handling and redaction policy for Agentopia in its current scaffold state.

## Goals

- keep persisted artifacts private by default
- reduce accidental persistence of obvious secret material
- make redaction behavior explicit and testable

## Current baseline

Artifacts and persisted run results should be treated as internal-only by default.

Minimum policy:

- persisted run outputs are written under internal repo-controlled paths
- artifact and persistence paths should not be treated as public URLs
- obvious secret-bearing keys should be redacted before persistence
- sensitive access tokens should not be written verbatim to persisted result payloads

## Redaction scope

At minimum, redact values for keys matching patterns like:

- `api_key`
- `token`
- `secret`
- `password`
- `authorization`

This baseline is heuristic, not perfect, but it is better than persisting raw values.

## Access control expectations

Current scaffold expectation:

- `var/hermes/` is internal workspace state, not a public artifact surface
- persisted result files should remain local/internal-only
- future public artifact access should require an explicit access-control layer, not direct filesystem exposure

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_persistence_redaction.py
```

## Definition of done for this item

This repo can consider artifact access controls and sensitive-output redaction minimally defined when:

- the artifact access expectation is documented
- persistence redacts obvious secret-bearing values
- redaction behavior is covered by tests
