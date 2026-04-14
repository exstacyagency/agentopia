#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-provenance.py"


class ProvenanceChecksTests(unittest.TestCase):
    def test_current_repo_passes_provenance_checks(self) -> None:
        result = subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("provenance checks ok", result.stdout)

    def test_unpinned_lockfile_line_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "requirements.lock").write_text("jsonschema>=4.23.0\n")
            config_dir = tmp / "config" / "environments"
            config_dir.mkdir(parents=True)
            (config_dir / "production.env").write_text(
                "PAPERCLIP_IMAGE=paperclipai/paperclip@sha256:" + "a" * 64 + "\n"
                "HERMES_IMAGE=ghcr.io/hermes-agent/hermes@sha256:" + "b" * 64 + "\n"
            )
            scripts_dir = tmp / "scripts"
            scripts_dir.mkdir(parents=True)
            script_copy = scripts_dir / "check-provenance.py"
            script_copy.write_text(SCRIPT.read_text())
            result = subprocess.run(["python3", str(script_copy)], cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dependency must use exact == pin", result.stdout)


if __name__ == "__main__":
    unittest.main()
