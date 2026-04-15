#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class BackupRestoreChecklistTests(unittest.TestCase):
    def test_checklist_reports_sqlite_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            db_path.write_text("placeholder")
            backup_dir = Path(tmp) / "backups"
            result = subprocess.run(
                [str(ROOT / "scripts" / "backup-restore-checklist.sh")],
                env={
                    "PAPERCLIP_DB_PATH": str(db_path),
                    "BACKUP_DIR": str(backup_dir),
                },
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("backend: sqlite", result.stdout)
            self.assertIn("sqlite_db: present", result.stdout)
            self.assertIn(str(backup_dir), result.stdout)


if __name__ == "__main__":
    unittest.main()
