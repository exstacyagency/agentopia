#!/usr/bin/env python3
from __future__ import annotations

import time
import unittest
from pathlib import Path

from hermes.runner import CommandRequest, ExecutionLimitError, SandboxAdapterRunner


class SlowAdapter:
    def run(self, request: CommandRequest) -> dict:
        time.sleep(1.2)
        return {"status": "ok", "command": request.command}


class ExecutionLimitTests(unittest.TestCase):
    def test_runner_enforces_runtime_limit(self) -> None:
        runner = SandboxAdapterRunner(SlowAdapter())
        with self.assertRaises(ExecutionLimitError):
            runner.run(CommandRequest(command="echo hi", cwd=Path.cwd(), max_runtime_seconds=1))


if __name__ == "__main__":
    unittest.main()
