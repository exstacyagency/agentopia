#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RenderProductionEnvTests(unittest.TestCase):
    def test_rendered_env_is_created_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            shutil.copytree(ROOT / "config", tmp / "config")
            shutil.copytree(ROOT / "scripts", tmp / "scripts")
            (tmp / "config" / "environments" / "production.secrets.env").write_text(
                "PAPERCLIP_API_KEY=prod-secret\nHERMES_API_KEY=prod-hermes-secret\n"
            )
            result = subprocess.run(
                ["bash", "scripts/render-production-env.sh"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            rendered = tmp / "config" / "environments" / "production.rendered.env"
            self.assertTrue(rendered.exists())
            content = rendered.read_text()
            self.assertIn("PAPERCLIP_API_KEY=prod-secret", content)
            self.assertIn("HERMES_API_KEY=prod-hermes-secret", content)


if __name__ == "__main__":
    unittest.main()
