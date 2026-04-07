from __future__ import annotations

from pathlib import Path

from hermes.file_ops import FileWriteError, write_workspace_file
from hermes.policy import evaluate_task_policy
from scripts.contracts import validate_payload

SUPPORTED_TASK_TYPES = {"repo_summary", "file_analysis", "text_generation", "structured_extract", "repo_change_plan", "implementation_draft", "repo_write", "file_write", "shell_command"}


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
        policy = evaluate_task_policy(payload)
        if task["type"] not in SUPPORTED_TASK_TYPES:
            return self.failure_result(
                task_id=task["id"],
                trace_id=payload["trace"]["trace_id"],
                code="EXECUTION_FAILED",
                message=f"unsupported task type: {task['type']}",
                retryable=False,
                metadata={
                    "task_type": task["type"],
                    "policy": {
                        "mode": "deny",
                        "reason": "unsupported_task_type",
                    },
                },
            )

        if not policy.allowed:
            return self.failure_result(
                task_id=task["id"],
                trace_id=payload["trace"]["trace_id"],
                code="POLICY_BLOCKED",
                message=f"task type blocked by policy: {task['type']}",
                retryable=False,
                metadata={
                    "task_type": task["type"],
                    "policy": {
                        "mode": policy.mode,
                        "reason": policy.reason,
                    },
                },
            )

        file_write = None
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
        elif task["type"] == "repo_change_plan":
            summary = self.build_repo_change_plan(task)
            result_summary = f"Repo change plan completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes repo_change_plan task",
                "Generated v1 result envelope",
            ]
        elif task["type"] == "implementation_draft":
            summary = self.build_implementation_draft(task)
            result_summary = f"Implementation draft completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Executed Hermes implementation_draft task",
                "Generated v1 result envelope",
            ]
        elif task["type"] == "file_write":
            try:
                file_write = self.build_file_write(task)
            except FileWriteError as exc:
                return self.failure_result(
                    task_id=task["id"],
                    trace_id=payload["trace"]["trace_id"],
                    code="WRITE_SCOPE_VIOLATION",
                    message=str(exc),
                    retryable=False,
                    metadata={
                        "task_type": task["type"],
                        "policy": {
                            "mode": policy.mode,
                            "reason": policy.reason,
                        },
                    },
                )
            summary = file_write["summary"]
            result_summary = f"File write completed for {task['title']}"
            notes = [
                "Validated request payload",
                "Policy-approved Hermes file_write task",
                "Performed workspace-scoped file write",
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
        artifacts = [
            {
                "type": "structured_output",
                "path": "artifacts/output.json",
                "content_type": "application/json",
                "metadata": {
                    "task_type": task["type"],
                    "task_id": task["id"],
                },
            }
        ]
        if file_write:
            artifacts.append(
                {
                    "type": "file_write",
                    "path": file_write["relative_path"],
                    "content_type": "text/plain",
                    "metadata": {
                        "task_type": task["type"],
                        "task_id": task["id"],
                        "bytes_written": file_write["bytes_written"],
                        "existed_before": file_write["existed_before"],
                        "changed": file_write["changed"],
                        "previous_bytes": file_write["previous_bytes"],
                        "previous_sha256": file_write["previous_sha256"],
                        "new_sha256": file_write["new_sha256"],
                        "change_preview": file_write["change_preview"],
                        "overwrite": file_write["overwrite"],
                    },
                }
            )

        metadata = {
            "task_type": task["type"],
            "paperclip_issue_id": context.get("issue_id"),
            "paperclip_run_id": context.get("paperclip_run_id"),
            "agent_id": context.get("agent_id"),
            "context": context,
            "policy": {
                "mode": policy.mode,
                "reason": policy.reason,
            },
        }
        if file_write:
            metadata["file_write"] = {
                "path": file_write["relative_path"],
                "bytes_written": file_write["bytes_written"],
                "existed_before": file_write["existed_before"],
                "changed": file_write["changed"],
                "previous_bytes": file_write["previous_bytes"],
                "previous_sha256": file_write["previous_sha256"],
                "new_sha256": file_write["new_sha256"],
                "change_preview": file_write["change_preview"],
                "overwrite": file_write["overwrite"],
            }

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
                "metadata": metadata,
                "error": None,
            },
            "artifacts": artifacts,
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

    def build_structured_extract(self, task: dict) -> str:
        context = task.get("context", {})
        source = context.get("source") or context.get("file_path") or "unknown-source"
        extraction_goal = context.get("extraction_goal") or task["description"]
        output_schema = context.get("output_schema") or ["items", "notes"]
        return "\n".join(
            [
                "# Structured Extract",
                f"- Source: {source}",
                f"- Extraction goal: {extraction_goal}",
                f"- Output schema: {output_schema}",
                "",
                "Extracted structure:",
                "- items: []",
                "- notes: ['structured extraction scaffold completed']",
            ]
        )

    def build_repo_change_plan(self, task: dict) -> str:
        context = task.get("context", {})
        repo = context.get("repo") or "unknown-repo"
        goal = context.get("goal") or task["description"]
        impacted_files = context.get("impacted_files") or ["TBD"]
        return "\n".join(
            [
                "# Repo Change Plan",
                f"- Repo: {repo}",
                f"- Goal: {goal}",
                f"- Impacted files: {impacted_files}",
                "",
                "Plan:",
                "1. Inspect the relevant files and existing behavior.",
                "2. Identify the smallest safe set of changes.",
                "3. Define validation and rollback checks.",
                "",
                "Risks:",
                "- hidden coupling in adjacent modules",
                "- stale assumptions in local-only Paperclip patches",
            ]
        )

    def build_implementation_draft(self, task: dict) -> str:
        context = task.get("context", {})
        goal = context.get("goal") or task["description"]
        impacted_files = context.get("impacted_files") or ["TBD"]
        validation_checks = context.get("validation_checks") or ["Run targeted tests", "Review edge cases"]
        return "\n".join(
            [
                "# Implementation Draft",
                f"- Goal: {goal}",
                f"- Impacted files: {impacted_files}",
                f"- Validation checks: {validation_checks}",
                "",
                "Draft plan:",
                "1. Inspect current behavior and constraints.",
                "2. Draft the minimal code changes required.",
                "3. Identify follow-up validation and rollback checks.",
                "",
                "Proposed edit sketch:",
                "- TODO: add implementation outline here",
            ]
        )

    def build_file_write(self, task: dict) -> dict:
        context = task.get("context", {})
        file_path = context.get("file_path") or ""
        content = context.get("content") or ""
        overwrite = bool(context.get("overwrite", False))
        write_result = write_workspace_file(self.root, file_path, content, overwrite=overwrite)
        relative_path = str(write_result.path.relative_to(self.root))
        status = "updated" if write_result.existed_before and write_result.changed else "created"
        if write_result.existed_before and not write_result.changed:
            status = "unchanged"
        return {
            "relative_path": relative_path,
            "bytes_written": write_result.bytes_written,
            "existed_before": write_result.existed_before,
            "changed": write_result.changed,
            "previous_bytes": write_result.previous_bytes,
            "previous_sha256": write_result.previous_sha256,
            "new_sha256": write_result.new_sha256,
            "change_preview": write_result.change_preview,
            "overwrite": overwrite,
            "summary": "\n".join(
                [
                    "# File Write",
                    f"- File: {relative_path}",
                    f"- Bytes: {write_result.bytes_written}",
                    f"- Previous bytes: {write_result.previous_bytes}",
                    f"- Overwrite: {overwrite}",
                    f"- Previous hash: {write_result.previous_sha256}",
                    f"- New hash: {write_result.new_sha256}",
                    f"- Change preview: {write_result.change_preview}",
                    f"- Status: {status}",
                    "",
                    "Written content:",
                    content,
                ]
            ),
        }

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

    def failure_result(self, task_id: str, trace_id: str, code: str, message: str, retryable: bool, metadata: dict | None = None) -> dict:
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
                "metadata": metadata or {},
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
