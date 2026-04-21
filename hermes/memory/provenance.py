from __future__ import annotations

from typing import Any


def extract_memory_provenance(result: dict[str, Any]) -> dict[str, Any] | None:
    memory = (((result or {}).get("result") or {}).get("metadata") or {}).get("memory")
    if not isinstance(memory, dict):
        return None
    hits = memory.get("memory_hits") or []
    return {
        "tenant_id": memory.get("tenant_id", ""),
        "org_id": memory.get("org_id", ""),
        "client_id": memory.get("client_id", ""),
        "memory_mode": memory.get("memory_mode"),
        "memory_source": memory.get("memory_source"),
        "memory_hit_count": len(hits) if isinstance(hits, list) else 0,
    }
