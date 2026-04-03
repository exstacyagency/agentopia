#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from contract_runner import ContractRunner
from output_models import HandoffPolicy, TaskOutput


class TaskRunner(ContractRunner):
    @property
    def output_path(self) -> Path:
        return self.artifacts / "output.json"

    @property
    def fixture_path(self) -> Path:
        return self.root / "scripts" / "output_fixture.json"

    def build_output(self, task: dict) -> TaskOutput:
        return TaskOutput(
            task_id=task["id"],
            title=task["title"],
            priority=task["priority"],
            policy=HandoffPolicy(
                budget_usd=task["budget"]["maxCostUsd"],
                runtime_minutes=task["budget"]["maxRuntimeMinutes"],
                approval_required=task["approval"]["required"],
            ),
            summary=f"Completed task: {task['title']}",
            notes=(
                "Validated request contract",
                "Validated budget/approval policy",
                "Wrote structured output",
            ),
        )

    def write_result(self, task: dict) -> None:
        output = self.build_output(task)
        result = {
            "result": {
                "taskId": output.task_id,
                "status": output.status,
                "summary": output.summary,
                "artifacts": ["README.md", "docs/example-flow.md", "artifacts/result.json", "artifacts/output.json"],
                "audit": {
                    "approvedBy": output.handoff_from,
                    "executedBy": output.handoff_to,
                    "runtimeSeconds": 12,
                },
            }
        }
        output_dict = {
            "task": {
                "id": output.task_id,
                "title": output.title,
                "priority": output.priority,
            },
            "handoff": {
                "from": output.handoff_from,
                "to": output.handoff_to,
                "policy": {
                    "budgetUsd": output.policy.budget_usd,
                    "runtimeMinutes": output.policy.runtime_minutes,
                    "approvalRequired": output.policy.approval_required,
                },
            },
            "execution": {
                "status": output.status,
                "summary": output.summary,
                "notes": list(output.notes),
            },
        }
        self.require_keys(result, "result envelope", {"result"})
        self.require_keys(result["result"], "result", {"taskId", "status", "summary", "artifacts", "audit"})
        self.require_keys(output_dict, "output envelope", {"task", "handoff", "execution"})
        self.require_keys(output_dict["task"], "output.task", {"id", "title", "priority"})
        self.require_keys(output_dict["handoff"], "output.handoff", {"from", "to", "policy"})
        self.require_keys(output_dict["handoff"]["policy"], "output.handoff.policy", {"budgetUsd", "runtimeMinutes", "approvalRequired"})
        self.require_keys(output_dict["execution"], "output.execution", {"status", "summary", "notes"})
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.result_path.write_text(json.dumps(result, indent=2) + "\n")
        self.output_path.write_text(json.dumps(output_dict, indent=2) + "\n")
        (self.artifacts / "summary.txt").write_text(output.summary + "\n")


def main() -> int:
    runner = TaskRunner(Path(__file__).resolve().parent.parent)
    runner.run()
    print("task runner ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
