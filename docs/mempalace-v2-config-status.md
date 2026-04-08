# MemPalace V2 Config and Status

This document describes the next MemPalace integration step after search and wakeup context: configuration and status surfaces.

## Endpoints

### Get config
```bash
GET /internal/memory/config
```

### Set config
```bash
POST /internal/memory/config
```

Payload:
```json
{
  "enabled": true,
  "command": "mempalace",
  "palace_path": "/path/to/palace"
}
```

### Status
```bash
GET /internal/memory/status
```

## What status returns
- current config
- whether the configured MemPalace command is found
- any command-level error

## Why this matters

These endpoints are the minimum backend contract needed before a Paperclip company-level Memory tab can show and edit real MemPalace settings.
