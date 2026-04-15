from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class SandboxDeniedError(RuntimeError):
    pass


@dataclass
class CommandRequest:
    command: str
    cwd: Path


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
        return self.adapter.run(request)
