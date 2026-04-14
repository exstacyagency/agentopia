# Metrics

This document defines the minimum metrics baseline for Agentopia in its current scaffold state.

## Goals

- expose a simple machine-readable metrics surface
- count important request and rejection events
- make service activity visible without requiring log scraping

## Current baseline

Paperclip and Hermes should expose a basic Prometheus-style metrics endpoint.

Minimum counters:

- requests received
- responses sent
- requests rejected

## Current endpoints

- `GET /metrics` on Paperclip
- `GET /metrics` on Hermes

## Format

Current metrics output is plain text in a simple Prometheus-compatible exposition style.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_metrics.py
```

## Definition of done for this item

This repo can consider metrics minimally defined when:

- both services expose a metrics endpoint
- important request/response/rejection counters are tracked
- behavior is documented and tested
