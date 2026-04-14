# Correlation IDs Across Requests and Runs

This document defines the minimum correlation ID baseline for Agentopia in its current scaffold state.

## Goals

- make related Paperclip and Hermes logs easier to connect
- propagate a stable request correlation token across internal calls
- surface correlation IDs in HTTP responses for easier debugging

## Current baseline

Agentopia should use `X-Correlation-ID` as the internal request correlation header.

Behavior:

- if the inbound request already provides `X-Correlation-ID`, preserve it
- otherwise generate a correlation ID at the service boundary
- include the correlation ID in structured logs
- forward the correlation ID on internal Paperclip → Hermes dispatches
- return the correlation ID in HTTP responses

## Current scope

- Paperclip request handling
- Hermes request handling
- Paperclip internal dispatch client

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_correlation_ids.py
```

## Definition of done for this item

This repo can consider correlation IDs minimally defined when:

- both services attach correlation IDs to logs and responses
- internal dispatch propagates the correlation ID header
- behavior is documented and tested
