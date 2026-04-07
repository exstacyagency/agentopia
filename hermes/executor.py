from __future__ import annotations

from pathlib import Path

from scripts.contracts import validate_payload

SUPPORTED_TASK_TYPES = {"repo_summary", "file_analysis", "text_generation", "structured_extract"}


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

        if task["type"] == "repo_summary":
            summary = self.build_repo_summary(task)
            result_summary = f"Repository summary completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes repo_summary task",
                "Generated v1 result envelope",
            ]
        elif task["type"] == "file_analysis":
            summary = self.build_file_analysis(task)
            result_summary = f"File analysis completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes file_analysis task",
                "Generated v1 result envelope",
            ]
        elif task["type"] == "structured_extract":
            summary = self.build_structured_extract(task)
            result_summary = f"Structured extraction completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes structured_extract task",
                "Generated v1 result envelope",
            ]
        else:
            summary = self.build_text_generation(task)
            result_summary = f"Text generation completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes text_generation task",
                "Generated v1 result envelope",
            ]

        context = task.get("context", {})
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
                "summary": result_summary,
                "output_format": "markdown",
                "output": summary,
                "notes": notes,
                "metadata": {
                    "task_type": task["type"],
                    "paperclip_issue_id": context.get("issue_id"),
                    "paperclip_run_id": context.get("paperclip_run_id"),
                    "agent_id": context.get("agent_id"),
                    "context": context,
                },
                "error": None,
            },
            "artifacts": [
                {
                    "type": "structured_output",
                    "path": "artifacts/output.json",
                    "content_type": "application/json",
                    "metadata": {
                        "task_type": task["type"],
                        "task_id": task["id"],
                    },
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
                "# Repo Summary",
                f"- Repo: {repo}",
                f"- Branch: {branch}",
                f"- Task: {task['title']}",
                f"- Description: {task['description']}",
            ]
        )

    def build_file_analysis(self, task: dict) -> str:
        context = task.get("context", {})
        file_path = context.get("file_path") or context.get("path") or "unknown-file"
        objective = context.get("objective") or task["description"]
        return "\n".join(
            [
                "# File Analysis",
                f"- File: {file_path}",
                f"- Objective: {objective}",
                f"- Task: {task['title']}",
                "- Status: analysis scaffold completed",
            ]
        )

    def build_text_generation(self, task: dict) -> str:
        context = task.get("context", {})
        prompt = context.get("prompt") or task["description"]
        audience = context.get("audience") or "general"
        tone = context.get("tone") or "neutral"
        return "\n".join(
            [
                "# Text Generation",
                f"- Audience: {audience}",
                f"- Tone: {tone}",
                f"- Task: {task['title']}",
                "",
                "Generated draft:",
                f"{prompt}",
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
