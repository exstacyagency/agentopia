from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path


class SandboxDeniedError(RuntimeError):
    pass


class ExecutionLimitError(RuntimeError):
    pass


@dataclass
class CommandRequest:
    command: str
    cwd: Path
    max_runtime_seconds: int | None = None


class CommandRunner:
    def run(self, request: CommandRequest) -> dict:
        raise NotImplementedError


class DenyByDefaultRunner(CommandRunner):
    def run(self, request: CommandRequest) -> dict:
        raise SandboxDeniedError(f"sandbox denied command execution: {request.command}")


class SandboxAdapterRunner(CommandRunner):
    def __init__(self, adapter):
        self.adapter = adapter

    def run(self, request: CommandRequest) -> dict:
        started = time.monotonic()
        result = self.adapter.run(request)
        if request.max_runtime_seconds is not None and time.monotonic() - started > request.max_runtime_seconds:
            raise ExecutionLimitError(f"command exceeded runtime limit of {request.max_runtime_seconds} seconds")
        return result
