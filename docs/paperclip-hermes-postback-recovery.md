# Paperclip ↔ Hermes Postback Recovery

This document describes the postback recovery hardening layer for Paperclip comments and dashboard documents.

## What is recorded

Paperclip postbacks now persist records under:
- `var/hermes/postbacks/`

Each record includes:
- issue id
- run id
- postback type (`comment` or `dashboard`)
- success flag
- error string when present
- retryable flag
- stored payload details

## Scripts

### List failed postbacks

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_failed_postbacks.py
```

### Retry postbacks

```bash
python3 scripts/retry_postbacks.py
```

Current status:
- records are durable
- failed postbacks are inspectable
- retry script now performs real replay for comment and dashboard postbacks
- replay updates the stored record in place with success/failure status

## Why this matters

This reduces one of the main operational blind spots in the platform:
Paperclip comment/document failures are now durable and diagnosable instead of only appearing as transient runtime errors.
