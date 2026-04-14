#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-secret-handling.py"


class SecretHandlingTests(unittest.TestCase):
    def test_current_repo_passes_secret_handling_checks(self) -> None:
        result = subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("secret handling checks ok", result.stdout)

    def test_forbidden_secret_pattern_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / ".gitignore").write_text("config/environments/*.secrets.env\nconfig/environments/*.rendered.env\n")
            env_dir = tmp / "config" / "environments"
            env_dir.mkdir(parents=True)
            (tmp / ".env.example").write_text("NODE_ENV=development\n")
            (env_dir / "development.env").write_text("PAPERCLIP_API_KEY=dev-key\n")
            (env_dir / "staging.env").write_text("HERMES_API_KEY=staging-key\n")
            (env_dir / "production.env").write_text("PAPERCLIP_API_KEY=production-real-secret\n")
            scripts_dir = tmp / "scripts"
            scripts_dir.mkdir(parents=True)
            script_copy = scripts_dir / "check-secret-handling.py"
            script_copy.write_text(SCRIPT.read_text())
            result = subprocess.run(["python3", str(script_copy)], cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden secret-like pattern", result.stdout)


if __name__ == "__main__":
    unittest.main()
