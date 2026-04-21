#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes.memory.config import require_memory_scope, tenant_config_path, tenant_status_path
from hermes.memory.service import MemPalaceService


class MemoryDeletionWorkflowTests(unittest.TestCase):
    def test_delete_removes_only_target_tenant_memory(self) -> None:
        service = MemPalaceService()
        with tempfile.TemporaryDirectory() as tmp:
            memory_root = Path(tmp)
            with patch("hermes.memory.config.MEMORY_ROOT", memory_root):
                service.set_config({"tenant_id": "tenant-a"}, {"enabled": True, "command": "mempalace-a", "memory_mode": "augment"})
                service.set_config({"tenant_id": "tenant-b"}, {"enabled": True, "command": "mempalace-b", "memory_mode": "augment"})
                service._write_status_file(require_memory_scope({"tenant_id": "tenant-a"}), {"last_operation": "mine", "last_synced_at": "now", "last_error": None})
                service._write_status_file(require_memory_scope({"tenant_id": "tenant-b"}), {"last_operation": "mine", "last_synced_at": "now", "last_error": None})

                tenant_a_config = tenant_config_path(require_memory_scope({"tenant_id": "tenant-a"}))
                tenant_b_config = tenant_config_path(require_memory_scope({"tenant_id": "tenant-b"}))
                tenant_a_status = tenant_status_path(require_memory_scope({"tenant_id": "tenant-a"}))
                tenant_b_status = tenant_status_path(require_memory_scope({"tenant_id": "tenant-b"}))

                self.assertTrue(tenant_a_config.exists())
                self.assertTrue(tenant_b_config.exists())
                self.assertTrue(tenant_a_status.exists())
                self.assertTrue(tenant_b_status.exists())

                deleted_paths = []

                def fake_rmtree(path) -> None:
                    deleted_paths.append(str(path))
                    target = Path(path)
                    if target.exists():
                        for child in sorted(target.rglob("*"), reverse=True):
                            if child.is_file():
                                child.unlink()
                            elif child.is_dir():
                                child.rmdir()
                        target.rmdir()

                with patch("hermes.memory.config.shutil.rmtree", fake_rmtree):
                    result = service.delete({"tenant_id": "tenant-a"})

                self.assertTrue(result["deleted"])
                self.assertEqual(result["scope"]["tenant_id"], "tenant-a")
                self.assertFalse(tenant_a_config.exists())
                self.assertFalse(tenant_a_status.exists())
                self.assertTrue(tenant_b_config.exists())
                self.assertTrue(tenant_b_status.exists())
                self.assertEqual(len(deleted_paths), 1)
                self.assertIn("tenant-a", deleted_paths[0])

    def test_delete_reports_already_absent_when_tenant_memory_missing(self) -> None:
        service = MemPalaceService()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("hermes.memory.config.MEMORY_ROOT", Path(tmp)):
                result = service.delete({"tenant_id": "tenant-missing"})
                self.assertEqual(result["reason"], "tenant_memory_already_absent")
                self.assertFalse(result["deleted"])


if __name__ == "__main__":
    unittest.main()
