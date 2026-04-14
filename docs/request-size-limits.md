# Request Size Limits

This document defines the minimum request size limit policy for Agentopia in its current scaffold state.

## Goals

- reduce oversized request abuse
- bound request memory usage in the simple HTTP server layer
- keep limits explicit and configurable

## Current baseline

Both Paperclip and Hermes should reject oversized POST bodies before attempting to parse them.

Default limit:

- `1 MiB` request body size cap

Config:

- `PAPERCLIP_MAX_REQUEST_BYTES`
- `HERMES_MAX_REQUEST_BYTES`

## Expected behavior

If a request exceeds the configured limit:

- return HTTP `413`
- return a small JSON error payload
- do not attempt JSON decoding

If `Content-Length` is missing, the current scaffold treats the body as empty unless data is read through other means.

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_request_limits.py
```

## Definition of done for this item

This repo can consider request size limits minimally defined when:

- both HTTP services enforce a request body limit
- the limit is configurable via env vars
- oversized requests return `413`
- behavior is documented and tested
