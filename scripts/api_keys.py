from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiKeyIdentity:
    key_id: str
    scope: str


def _fingerprint(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()[:12]


def resolve_api_key_identity(authorization_header: str, configured_keys: str) -> ApiKeyIdentity | None:
    if not configured_keys:
        return None
    if not authorization_header.startswith("Bearer "):
        return None
    provided = authorization_header.removeprefix("Bearer ").strip()
    if not provided:
        return None

    for entry in configured_keys.split(","):
        item = entry.strip()
        if not item:
            continue
        try:
            scope, raw_key = item.split(":", 1)
        except ValueError:
            continue
        scope = scope.strip()
        raw_key = raw_key.strip()
        if scope and raw_key and provided == raw_key:
            return ApiKeyIdentity(key_id=_fingerprint(raw_key), scope=scope)
    return None


def configured_client_api_keys() -> str:
    return os.environ.get("PAPERCLIP_CLIENT_API_KEYS", "")
