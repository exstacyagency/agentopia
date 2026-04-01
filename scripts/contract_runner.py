from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContractRunner:
    root: Path

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def request_path(self) -> Path:
        return self.artifacts / "request.json"

    @property
    def result_path(self) -> Path:
        return self.artifacts / "result.json"

    def load_request(self) -> dict:
        return json.loads(self.request_path.read_text())

    def require_keys(self, obj: dict, parent: str, keys: set[str]) -> None:
        missing = sorted(keys - set(obj.keys()))
        assert not missing, f"{parent} missing keys: {', '.join(missing)}"

    def validate_request(self, request: dict) -> dict:
        self.require_keys(request, "request", {"task"})
        task = request["task"]
        self.require_keys(task, "task", {"id", "title", "priority", "requester", "budget", "approval", "constraints", "routing"})
        self.require_keys(task["requester"], "task.requester", {"id", "displayName"})
        self.require_keys(task["budget"], "task.budget", {"maxCostUsd", "maxRuntimeMinutes"})
        self.require_keys(task["approval"], "task.approval", {"required"})
        self.require_keys(task["constraints"], "task.constraints", {"outputFormat", "outputLength", "allowNetwork"})
        self.require_keys(task["routing"], "task.routing", {"inbound", "outbound"})
        assert task["routing"]["inbound"] == "paperclip"
        assert task["routing"]["outbound"] == "hermes"
        assert task["approval"]["required"] is False
        return task

    def write_result(self, task: dict) -> None:
        result = {
            "result": {
                "taskId": task["id"],
                "status": "success",
                "summary": "Repository scaffold updated and documented.",
                "artifacts": ["README.md", "docs/example-flow.md"],
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

    def run(self) -> None:
        request = self.load_request()
        task = self.validate_request(request)
        self.write_result(task)
