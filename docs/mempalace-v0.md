# MemPalace V0

This document describes the first implementation step for MemPalace integration in Agentopia.

## Scope

V0 is intentionally minimal:
- Agentopia-side MemPalace client
- Agentopia-side service/config loader
- one working internal endpoint
- no Paperclip UI yet

## Added files

- `hermes/memory/config.py`
- `hermes/memory/mempalace_client.py`
- `hermes/memory/service.py`

## Endpoint

```bash
POST /internal/memory/search
```

Payload:

```json
{
  "query": "search text"
}
```

## Behavior

When disabled:
- returns `mempalace_disabled`

When command is missing:
- returns `mempalace_command_not_found`

When search works:
- returns `mempalace_search_ok`
- includes parsed results

## Configuration

Environment variables:
- `MEMPALACE_ENABLED=1`
- `MEMPALACE_COMMAND=mempalace`

## Why this is first

This proves the platform can:
- talk to MemPalace from Agentopia/Hermes
- return memory results through a stable internal contract
- support a future Paperclip Memory tab without making the UI guess
