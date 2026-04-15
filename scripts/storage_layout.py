from __future__ import annotations

import json
import shutil
from pathlib import Path


class PaperclipStorageLayout:
    def __init__(self, root: Path):
        self.root = root

    def task_dir(self, task_id: str) -> Path:
        return self.root / "var" / "paperclip" / "tasks" / task_id

    def artifacts_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "artifacts"

    def result_path(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "result.json"

    def ensure_task_dirs(self, task_id: str) -> None:
        self.artifacts_dir(task_id).mkdir(parents=True, exist_ok=True)

    def persist_result(self, task_id: str, payload: dict) -> Path:
        self.ensure_task_dirs(task_id)
        path = self.result_path(task_id)
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path

    def delete_task_storage(self, task_id: str) -> None:
        task_dir = self.task_dir(task_id)
        if task_dir.exists():
            shutil.rmtree(task_dir)
