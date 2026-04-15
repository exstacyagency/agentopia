#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paperclip.db import PaperclipDB


class PostgresPersistenceTests(unittest.TestCase):
    def test_postgres_url_selects_postgres_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            os.environ["PAPERCLIP_DATABASE_URL"] = "postgresql://agentopia:secret@localhost:5432/agentopia"
            with patch("paperclip.db.PostgresPaperclipDB") as backend:
                backend.return_value = type("FakePostgresDB", (), {"conn": object()})()
                PaperclipDB(db_path)
                backend.assert_called_once()
        os.environ.pop("PAPERCLIP_DATABASE_URL", None)


if __name__ == "__main__":
    unittest.main()
