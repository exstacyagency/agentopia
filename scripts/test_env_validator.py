#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EnvValidatorTests(unittest.TestCase):
    def make_env(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return Path(tmp.name)

    def test_production_requires_digest_refs(self) -> None:
        env_path = self.make_env(
            "\n".join(
                [
                    "NODE_ENV=production",
                    "PAPERCLIP_URL=https://paperclip.example.com",
                    "PAPERCLIP_API_KEY=test",
                    "PAPERCLIP_IMAGE=paperclipai/paperclip:1.0.0",
                    "HERMES_MODEL_PROVIDER=openrouter",
                    "HERMES_MODEL=test-model",
                    "HERMES_API_KEY=test",
                    "HERMES_IMAGE=ghcr.io/hermes-agent/hermes:1.0.0",
                ]
            )
        )
        result = subprocess.run(
            ["python3", "scripts/env-validator.py", "--env-file", str(env_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("production requires a sha256 digest image ref", result.stdout)

    def test_staging_allows_explicit_tags(self) -> None:
        env_path = self.make_env(
            "\n".join(
                [
                    "NODE_ENV=staging",
                    "PAPERCLIP_URL=https://paperclip.staging.example.com",
                    "PAPERCLIP_API_KEY=test",
                    "PAPERCLIP_IMAGE=paperclipai/paperclip:1.0.0-rc1",
                    "HERMES_MODEL_PROVIDER=openrouter",
                    "HERMES_MODEL=test-model",
                    "HERMES_API_KEY=test",
                    "HERMES_IMAGE=ghcr.io/hermes-agent/hermes:1.0.0-rc1",
                ]
            )
        )
        result = subprocess.run(
            ["python3", "scripts/env-validator.py", "--env-file", str(env_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("env validation ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
