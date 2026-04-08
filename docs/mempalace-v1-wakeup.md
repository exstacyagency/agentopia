# MemPalace V1 Wakeup Context

This document describes the next MemPalace integration step after raw search: wakeup-context assembly.

## Endpoint

```bash
POST /internal/memory/wakeup
```

Payload:

```json
{
  "issue_title": "...",
  "issue_description": "..."
}
```

## Behavior

The endpoint:
1. builds a query from issue title + description
2. executes a MemPalace-backed search through the Agentopia memory service
3. returns a wakeup context object containing memory hits

## Response shape

```json
{
  "config": {
    "enabled": true,
    "command": "mempalace"
  },
  "ok": true,
  "reason": "mempalace_search_ok",
  "query": "...",
  "wakeup_context": {
    "issue_title": "...",
    "issue_description": "...",
    "memory_hits": []
  }
}
```

## Why this matters

This is the first memory-aware execution-facing contract in Agentopia.
It gives future Paperclip wakeup flows and Hermes execution paths a stable memory context surface to build on.
