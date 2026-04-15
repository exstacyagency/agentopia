from __future__ import annotations

import json
import time
from contextlib import contextmanager

from hermes.runner import ExecutionLimitError

DEFAULT_MAX_OUTPUT_BYTES = 64 * 1024


def max_runtime_seconds_for(task_request: dict) -> int | None:
    runtime_minutes = task_request.get("execution_policy", {}).get("budget", {}).get("max_runtime_minutes", 0)
    if not runtime_minutes:
        return None
    return max(1, int(runtime_minutes * 60))


def max_output_bytes_for(task_request: dict) -> int:
    return int(task_request.get("execution_policy", {}).get("budget", {}).get("max_output_bytes", DEFAULT_MAX_OUTPUT_BYTES))


@contextmanager
def enforce_execution_runtime(max_runtime_seconds: int | None):
    started = time.monotonic()
    yield
    if max_runtime_seconds is not None and time.monotonic() - started > max_runtime_seconds:
        raise ExecutionLimitError(f"execution exceeded runtime limit of {max_runtime_seconds} seconds")


def enforce_output_size(payload: dict, max_output_bytes: int) -> None:
    encoded = json.dumps(payload).encode()
    if len(encoded) > max_output_bytes:
        raise ExecutionLimitError(f"execution output exceeded limit of {max_output_bytes} bytes")
