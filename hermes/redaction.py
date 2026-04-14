from __future__ import annotations

from collections.abc import Mapping, Sequence

SENSITIVE_KEY_PARTS = ("api_key", "token", "secret", "password", "authorization")
REDACTED = "[REDACTED]"


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def redact_value(value):
    if isinstance(value, Mapping):
        return {k: (REDACTED if is_sensitive_key(str(k)) else redact_value(v)) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_value(item) for item in value]
    return value
