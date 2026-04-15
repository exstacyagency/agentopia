from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from hermes.runner import CommandRequest

SANDBOX_PROFILE = """
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
(deny network*)
"""


class MacOSSandboxAdapter:
    def run(self, request: CommandRequest) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            profile = SANDBOX_PROFILE.format(workspace=str(request.cwd), tmpdir=tmp)
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
