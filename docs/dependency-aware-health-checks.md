# Dependency-Aware Health Checks

This document defines the minimum dependency-aware health check baseline for Agentopia in its current scaffold state.

## Goals

- make health endpoints reflect dependency readiness, not just process liveness
- surface missing runtime prerequisites in service health responses
- keep the checks lightweight and deterministic

## Current baseline

### Paperclip
Paperclip health should reflect:

- database path accessibility
- configured internal auth token presence

### Hermes
Hermes health should reflect:

- configured Paperclip result URL presence
- configured internal auth token presence

## Expected behavior

Health endpoints should return:

- `ok: true` only when required dependencies/config are ready
- structured dependency details in the JSON response
- HTTP `200` when healthy
- HTTP `503` when a required dependency is not ready

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_health_checks.py
```

## Definition of done for this item

This repo can consider dependency-aware health checks minimally defined when:

- Paperclip and Hermes health endpoints report dependency readiness
- missing required dependencies/config cause unhealthy responses
- behavior is documented and tested
