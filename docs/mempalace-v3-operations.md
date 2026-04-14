# MemPalace V3 Operations

This document describes the first operational MemPalace controls added to the platform.

## New endpoints

### Run mine
```bash
POST /internal/memory/mine
```

### Run reindex
```bash
POST /internal/memory/reindex
```

## Status additions

`GET /internal/memory/status` now includes:
- `last_operation`
- `last_synced_at`
- `last_error`

## Why this matters

This makes the Memory tab operational, not just configurable:
- operators can trigger memory maintenance
- the platform can show the last memory operation state
