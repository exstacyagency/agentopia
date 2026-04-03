#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from contract_runner import ContractRunner


class TaskRunner(ContractRunner):
    @property
    def output_path(self) -> Path:
        return self.artifacts / "output.json"

    def write_result(self, task: dict) -> None:
        output = {
            "task": {
                "id": task["id"],
                "title": task["title"],
                "priority": task["priority"],
            },
            "handoff": {
                "from": "paperclip",
                "to": "hermes",
            },
            "execution": {
                "status": "success",
                "summary": f"Completed task: {task['title']}",
            },
        }
        result = {
            "result": {
                "taskId": task["id"],
                "status": "success",
                "summary": output["execution"]["summary"],
                "artifacts": ["README.md", "docs/example-flow.md", "artifacts/result.json", "artifacts/output.json"],
                "audit": {
                    "approvedBy": "paperclip",
                    "executedBy": "hermes",
                    "runtimeSeconds": 12,
                },
            }
        }
        self.require_keys(result, "result envelope", {"result"})
        self.require_keys(result["result"], "result", {"taskId", "status", "summary", "artifacts", "audit"})
        self.require_keys(output, "output envelope", {"task", "handoff", "execution"})
        self.require_keys(output["task"], "output.task", {"id", "title", "priority"})
        self.require_keys(output["handoff"], "output.handoff", {"from", "to"})
        self.require_keys(output["execution"], "output.execution", {"status", "summary"})
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.result_path.write_text(json.dumps(result, indent=2) + "\n")
        self.output_path.write_text(json.dumps(output, indent=2) + "\n")
        (self.artifacts / "summary.txt").write_text(output["execution"]["summary"] + "\n")


def main() -> int:
    runner = TaskRunner(Path(__file__).resolve().parent.parent)
    runner.run()
    print("task runner ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
