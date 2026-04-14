from __future__ import annotations

import uuid


CORRELATION_HEADER = "X-Correlation-ID"


def get_or_create_correlation_id(headers) -> str:
    existing = headers.get(CORRELATION_HEADER, "").strip()
    if existing:
        return existing
    return str(uuid.uuid4())
