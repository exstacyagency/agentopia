#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.runtimes import RuntimeTargets


class RuntimeTargetsTests(unittest.TestCase):
    def make_env(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return Path(tmp.name)

    def test_explicit_tags_are_allowed(self) -> None:
        env_path = self.make_env(
            "\n".join(
                [
                    "PAPERCLIP_IMAGE=paperclipai/paperclip:1.0.0",
                    "HERMES_IMAGE=ghcr.io/hermes-agent/hermes:1.0.0",
                    "PAPERCLIP_URL=http://localhost:3100",
                    "PAPERCLIP_API_KEY=test",
                    "HERMES_MODEL_PROVIDER=openrouter",
                    "HERMES_MODEL=test-model",
                    "HERMES_API_KEY=test",
                ]
            )
        )
        targets = RuntimeTargets.from_env(env_path)
        self.assertEqual(targets.invalid_images(), [])
        self.assertTrue(targets.ok())

    def test_digests_are_allowed(self) -> None:
        digest = "a" * 64
        env_path = self.make_env(
            "\n".join(
                [
                    f"PAPERCLIP_IMAGE=paperclipai/paperclip@sha256:{digest}",
                    f"HERMES_IMAGE=ghcr.io/hermes-agent/hermes@sha256:{digest}",
                    "PAPERCLIP_URL=http://localhost:3100",
                    "PAPERCLIP_API_KEY=test",
                    "HERMES_MODEL_PROVIDER=openrouter",
                    "HERMES_MODEL=test-model",
                    "HERMES_API_KEY=test",
                ]
            )
        )
        targets = RuntimeTargets.from_env(env_path)
        self.assertEqual(targets.invalid_images(), [])
        self.assertTrue(targets.ok())

    def test_floating_tags_are_rejected(self) -> None:
        env_path = self.make_env(
            "\n".join(
                [
                    "PAPERCLIP_IMAGE=paperclipai/paperclip:latest",
                    "HERMES_IMAGE=ghcr.io/hermes-agent/hermes:main",
                    "PAPERCLIP_URL=http://localhost:3100",
                    "PAPERCLIP_API_KEY=test",
                    "HERMES_MODEL_PROVIDER=openrouter",
                    "HERMES_MODEL=test-model",
                    "HERMES_API_KEY=test",
                ]
            )
        )
        targets = RuntimeTargets.from_env(env_path)
        invalid = targets.invalid_images()
        self.assertEqual(len(invalid), 2)
        self.assertFalse(targets.ok())


if __name__ == "__main__":
    unittest.main()
