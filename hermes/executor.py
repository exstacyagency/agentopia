from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.contracts import validate_payload

SUPPORTED_TASK_TYPES = {"repo_summary"}


@dataclass(frozen=True)
class ExecutionResult:
    payload: dict


class HermesExecutor:
    def __init__(self, root: Path):
        self.root = root

    def execute(self, payload: dict) -> dict:
        errors = validate_payload("task_request_v1.json", payload)
        if errors:
            task_id = payload.get("task", {}).get("id") or "unknown-task"
            trace_id = payload.get("trace", {}).get("trace_id") or "unknown-trace"
            return self.failure_result(
                task_id=task_id,
                trace_id=trace_id,
                code="VALIDATION_FAILED",
                message="; ".join(errors),
                retryable=False,
            )

        task = payload["task"]
        if task["type"] not in SUPPORTED_TASK_TYPES:
            return self.failure_result(
                task_id=task["id"],
                trace_id=payload["trace"]["trace_id"],
                code="EXECUTION_FAILED",
                message=f"unsupported task type: {task['type']}",
                retryable=False,
            )

        summary = self.build_repo_summary(task)
        return {
            "schema_version": "v1",
            "task_id": task["id"],
            "run": {
                "run_id": f"run_{task['id']}",
                "status": "succeeded",
                "started_at": payload["trace"]["submitted_at"],
                "finished_at": payload["trace"]["submitted_at"],
                "runtime_seconds": 0,
            },
            "result": {
                "summary": f"Repository summary completed for {task['title']}",
                "output_format": "markdown",
                "output": summary,
                "notes": [
                    "Validated request payload",
                    "Executed minimal Hermes repo_summary task",
                    "Generated v1 result envelope",
                ],
                "error": None,
            },
            "artifacts": [
                {
                    "type": "structured_output",
                    "path": "artifacts/output.json",
                    "content_type": "application/json",
                }
            ],
            "usage": {
                "estimated_cost_usd": 0.0,
                "actual_cost_usd": 0.0,
                "model_provider": "local",
                "model_name": "minimal-hermes",
                "tool_calls": 0,
            },
            "trace": {
                "trace_id": payload["trace"]["trace_id"],
                "reported_at": payload["trace"]["submitted_at"],
            },
        }

    def build_repo_summary(self, task: dict) -> str:
        context = task.get("context", {})
        repo = context.get("repo", "unknown-repo")
        branch = context.get("branch", "unknown-branch")
        return "\n".join(
            [
                f"# Repo Summary",
                f"- Repo: {repo}",
                f"- Branch: {branch}",
                f"- Task: {task['title']}",
                f"- Description: {task['description']}",
            ]
        )

    def failure_result(self, task_id: str, trace_id: str, code: str, message: str, retryable: bool) -> dict:
        return {
            "schema_version": "v1",
            "task_id": task_id,
            "run": {
                "run_id": f"run_{task_id}",
                "status": "failed",
                "started_at": "1970-01-01T00:00:00Z",
                "finished_at": "1970-01-01T00:00:00Z",
                "runtime_seconds": 0,
            },
            "result": {
                "summary": "Hermes execution failed",
                "output_format": "text",
                "output": "",
                "notes": [],
                "error": {
                    "code": code,
                    "message": message,
                    "retryable": retryable,
                },
            },
            "artifacts": [],
            "usage": {
                "actual_cost_usd": 0.0,
                "model_provider": "local",
                "model_name": "minimal-hermes",
                "tool_calls": 0,
            },
            "trace": {
                "trace_id": trace_id,
                "reported_at": "1970-01-01T00:00:00Z",
            },
        }
