#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from contract_runner import ContractRunner


class TaskRunner(ContractRunner):
    def write_result(self, task: dict) -> None:
        result = {
            "result": {
                "taskId": task["id"],
                "status": "success",
                "summary": f"Completed task: {task['title']}",
                "artifacts": ["README.md", "docs/example-flow.md", "artifacts/result.json"],
                "audit": {
                    "approvedBy": "paperclip",
                    "executedBy": "hermes",
                    "runtimeSeconds": 12,
                },
            }
        }
        self.require_keys(result, "result envelope", {"result"})
        self.require_keys(result["result"], "result", {"taskId", "status", "summary", "artifacts", "audit"})
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.result_path.write_text(json.dumps(result, indent=2) + "\n")
        (self.artifacts / "summary.txt").write_text(result["result"]["summary"] + "\n")


def main() -> int:
    runner = TaskRunner(Path(__file__).resolve().parent.parent)
    runner.run()
    print("task runner ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
