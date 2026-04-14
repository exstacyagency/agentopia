from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path


ROLE_SCOPES = {
    "submitter": {"tasks.write"},
    "viewer": set(),
}


@dataclass(frozen=True)
class ApiKeyIdentity:
    key_id: str
    scope: str
    status: str = "active"
    role: str | None = None


def _fingerprint(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()[:12]


def _extract_bearer_token(authorization_header: str) -> str | None:
    if not authorization_header.startswith("Bearer "):
        return None
    provided = authorization_header.removeprefix("Bearer ").strip()
    return provided or None


def resolve_api_key_identity(authorization_header: str, configured_keys: str) -> ApiKeyIdentity | None:
    if not configured_keys:
        return None
    provided = _extract_bearer_token(authorization_header)
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


def _default_registry_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "paperclip" / "client_api_keys.json"


def configured_client_api_keys() -> str:
    return os.environ.get("PAPERCLIP_CLIENT_API_KEYS", "")


def configured_client_api_keys_file() -> Path:
    return Path(os.environ.get("PAPERCLIP_CLIENT_API_KEYS_FILE", str(_default_registry_path())))


def role_allows_scope(role: str | None, required_scope: str) -> bool:
    if not role:
        return False
    return required_scope in ROLE_SCOPES.get(role, set())


def resolve_api_key_identity_from_file(authorization_header: str, registry_path: Path) -> ApiKeyIdentity | None:
    provided = _extract_bearer_token(authorization_header)
    if not provided or not registry_path.exists():
        return None

    payload = json.loads(registry_path.read_text())
    for item in payload.get("keys", []):
        key = str(item.get("key", "")).strip()
        scope = str(item.get("scope", "")).strip()
        role = str(item.get("role", "")).strip() or None
        key_id = str(item.get("id", "")).strip() or _fingerprint(key)
        status = str(item.get("status", "active")).strip() or "active"
        if role and not scope:
            allowed_scopes = sorted(ROLE_SCOPES.get(role, set()))
            scope = allowed_scopes[0] if allowed_scopes else ""
        if key and provided == key:
            return ApiKeyIdentity(key_id=key_id, scope=scope, status=status, role=role)
    return None
