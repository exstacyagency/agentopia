#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import manage_client_api_keys


class ManageClientApiKeysTests(unittest.TestCase):
    def test_issue_revoke_and_rotate_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "client_api_keys.json"

            manage_client_api_keys.main.__globals__["build_parser"]().parse_args
            manage_client_api_keys.issue_key(
                type("Args", (), {
                    "registry": registry,
                    "key_id": "tenant-a-primary",
                    "role": "submitter",
                    "tenant_id": "tenant-a",
                    "org_id": "org-a",
                    "client_id": "client-a",
                })
            )
            payload = json.loads(registry.read_text())
            self.assertEqual(len(payload["keys"]), 1)
            self.assertEqual(payload["keys"][0]["status"], "active")

            manage_client_api_keys.revoke_key(
                type("Args", (), {
                    "registry": registry,
                    "key_id": "tenant-a-primary",
                })
            )
            payload = json.loads(registry.read_text())
            self.assertEqual(payload["keys"][0]["status"], "revoked")

            manage_client_api_keys.rotate_key(
                type("Args", (), {
                    "registry": registry,
                    "key_id": "tenant-a-primary",
                    "new_key_id": "tenant-a-rotated",
                })
            )
            payload = json.loads(registry.read_text())
            self.assertEqual(len(payload["keys"]), 2)
            rotated = [item for item in payload["keys"] if item["id"] == "tenant-a-rotated"][0]
            self.assertEqual(rotated["status"], "active")


if __name__ == "__main__":
    unittest.main()
