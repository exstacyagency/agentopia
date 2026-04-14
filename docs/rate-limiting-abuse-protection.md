# Rate Limiting and Abuse Protection

This document defines the minimum rate limiting and abuse protection baseline for Agentopia in its current scaffold state.

## Goals

- reduce simple request flooding against the HTTP service layer
- bound repeated requests from the same client address
- keep abuse controls explicit, lightweight, and configurable

## Current baseline

Paperclip and Hermes should apply a simple per-IP request window limiter.

Default policy:

- 30 requests per 60-second window per client IP

Config:

- `PAPERCLIP_RATE_LIMIT_COUNT`
- `PAPERCLIP_RATE_LIMIT_WINDOW_SECONDS`
- `HERMES_RATE_LIMIT_COUNT`
- `HERMES_RATE_LIMIT_WINDOW_SECONDS`

## Expected behavior

If the caller exceeds the configured limit:

- return HTTP `429`
- return a small JSON error payload
- do not continue into deeper request handling

## Notes

This is a simple in-process limiter.
It is not a replacement for upstream gateway, CDN, WAF, or multi-instance distributed rate limiting.
It does provide a concrete abuse-control baseline inside the current scaffold.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_rate_limits.py
```

## Definition of done for this item

This repo can consider rate limiting and abuse protection minimally defined when:

- both HTTP services enforce a per-IP request window limit
- limits are configurable via env vars
- exceeded limits return `429`
- behavior is documented and tested
