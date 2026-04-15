from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from hermes.runner import CommandRequest

SANDBOX_PROFILE_TEMPLATE = """
(version 1)
(deny default)
(allow process*)
(allow file-read*)
(allow file-write*
    (subpath \"{workspace}\")
    (subpath \"{tmpdir}\")
)
(allow file-write-data
    (subpath \"{workspace}\")
    (subpath \"{tmpdir}\")
)
(allow file-write-mode
    (subpath \"{workspace}\")
    (subpath \"{tmpdir}\")
)
(allow file-write-create
    (subpath \"{workspace}\")
    (subpath \"{tmpdir}\")
)
{network_rule}
"""


class MacOSSandboxAdapter:
    def __init__(self, allow_network: bool = False):
        self.allow_network = allow_network

    def sandbox_profile(self, workspace: Path, tmpdir: str) -> str:
        network_rule = "(allow network*)" if self.allow_network else "(deny network*)"
        return SANDBOX_PROFILE_TEMPLATE.format(workspace=str(workspace), tmpdir=tmpdir, network_rule=network_rule)

    def run(self, request: CommandRequest) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.sandbox_profile(request.cwd, tmp)
            profile_path = Path(tmp) / "sandbox.sb"
            profile_path.write_text(profile)
            completed = subprocess.run(
                ["/usr/bin/sandbox-exec", "-f", str(profile_path), "/bin/sh", "-lc", request.command],
                cwd=request.cwd,
                capture_output=True,
                text=True,
                timeout=request.max_runtime_seconds,
            )
            if completed.returncode != 0:
                raise RuntimeError((completed.stderr or completed.stdout or "sandboxed command failed").strip())
            return {
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
            }
