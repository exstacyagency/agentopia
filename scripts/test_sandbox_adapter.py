#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hermes.runner import CommandRequest, SandboxAdapterRunner
from hermes.sandbox_adapter import MacOSSandboxAdapter


class SandboxAdapterTests(unittest.TestCase):
    def test_sandbox_adapter_allows_workspace_read_only_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = SandboxAdapterRunner(MacOSSandboxAdapter())
            request = CommandRequest(command="/bin/pwd", cwd=Path(tmp), max_runtime_seconds=5)
            result = runner.run(request)
            self.assertEqual(result["returncode"], 0)
            self.assertIn(str(Path(tmp)), result["stdout"])

    def test_sandbox_adapter_blocks_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = SandboxAdapterRunner(MacOSSandboxAdapter())
            request = CommandRequest(command="curl https://example.com", cwd=Path(tmp), max_runtime_seconds=5)
            with self.assertRaises(RuntimeError):
                runner.run(request)


if __name__ == "__main__":
    unittest.main()
