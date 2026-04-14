# Alerts

This document defines the minimum alerting baseline for Agentopia in its current scaffold state.

## Goals

- turn health and metrics signals into explicit operator action points
- keep alert criteria simple and easy to review
- connect alert conditions to the existing operator runbooks

## Current baseline

Agentopia should define baseline alert conditions for common service failures.

## Suggested alert conditions

### 1. Health endpoint unhealthy
Trigger when:
- Paperclip `/health` returns `503`
- Hermes `/health` returns `503`

### 2. Elevated rejected request rate
Trigger when:
- request rejection counters increase unexpectedly
- especially for repeated `429`, `400`, or `413` behavior

### 3. Internal auth failures
Trigger when:
- `401` responses appear on protected internal endpoints

### 4. Dependency scan or provenance failures in CI
Trigger when:
- dependency vulnerability scan fails
- provenance checks fail

## Current implementation scope

This repo does not yet integrate with a pager or external alerting backend.

Current baseline is:
- alert rules documented in-repo
- helper script to evaluate basic local alert conditions from health/metrics endpoints

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_alerts.py
```

## Definition of done for this item

This repo can consider alerts minimally defined when:

- baseline alert conditions are documented
- a helper exists to evaluate current health/metrics alert conditions
- behavior is covered by tests
