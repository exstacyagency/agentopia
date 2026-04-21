#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes.memory.config import require_memory_scope, tenant_config_path, tenant_status_path
from hermes.memory.service import MemPalaceService


class MemoryTenantBoundaryTests(unittest.TestCase):
    def test_memory_scope_requires_tenant_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "tenant_id is required"):
            require_memory_scope({})

    def test_config_and_status_paths_are_tenant_partitioned(self) -> None:
        scope_a = require_memory_scope({"tenant_id": "tenant-a", "org_id": "org-a", "client_id": "client-a"})
        scope_b = require_memory_scope({"tenant_id": "tenant-b", "org_id": "org-b", "client_id": "client-b"})
        self.assertNotEqual(tenant_config_path(scope_a), tenant_config_path(scope_b))
        self.assertNotEqual(tenant_status_path(scope_a), tenant_status_path(scope_b))
        self.assertIn("tenant-a", str(tenant_config_path(scope_a)))
        self.assertIn("tenant-b", str(tenant_status_path(scope_b)))

    def test_set_config_isolated_by_tenant(self) -> None:
        service = MemPalaceService()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("hermes.memory.config.MEMORY_ROOT", Path(tmp)):
                config_a = service.set_config({"tenant_id": "tenant-a"}, {"enabled": True, "command": "mempalace-a", "memory_mode": "augment"})
                config_b = service.set_config({"tenant_id": "tenant-b"}, {"enabled": False, "command": "mempalace-b", "memory_mode": "off"})
                loaded_a = service.get_config({"tenant_id": "tenant-a"})
                loaded_b = service.get_config({"tenant_id": "tenant-b"})
                self.assertEqual(config_a["command"], "mempalace-a")
                self.assertEqual(config_b["command"], "mempalace-b")
                self.assertEqual(loaded_a["command"], "mempalace-a")
                self.assertEqual(loaded_b["command"], "mempalace-b")
                self.assertNotEqual(loaded_a["scope"]["tenant_id"], loaded_b["scope"]["tenant_id"])

    def test_status_isolated_by_tenant(self) -> None:
        service = MemPalaceService()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("hermes.memory.config.MEMORY_ROOT", Path(tmp)):
                service._write_status_file(require_memory_scope({"tenant_id": "tenant-a"}), {"last_operation": "mine", "last_synced_at": "a", "last_error": None})
                service._write_status_file(require_memory_scope({"tenant_id": "tenant-b"}), {"last_operation": "reindex", "last_synced_at": "b", "last_error": "err"})
                status_a = service.status({"tenant_id": "tenant-a"})
                status_b = service.status({"tenant_id": "tenant-b"})
                self.assertEqual(status_a["last_operation"], "mine")
                self.assertEqual(status_b["last_operation"], "reindex")
                self.assertEqual(status_a["scope"]["tenant_id"], "tenant-a")
                self.assertEqual(status_b["scope"]["tenant_id"], "tenant-b")


if __name__ == "__main__":
    unittest.main()
