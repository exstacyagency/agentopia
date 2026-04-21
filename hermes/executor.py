from __future__ import annotations

from pathlib import Path

from hermes.action_labels import derive_action_labels
from hermes.execution_limits import enforce_execution_runtime, enforce_output_size, max_output_bytes_for, max_runtime_seconds_for
from hermes.file_ops import preview_change, revert_workspace_file, write_workspace_file
from hermes.memory.service import MemPalaceService
from hermes.network_policy import NetworkEgressDeniedError, enforce_network_policy
from hermes.repo_ops import apply_repo_write, preview_repo_write
from hermes.runner import CommandRequest, DenyByDefaultRunner, ExecutionLimitError, SandboxDeniedError
from hermes.shell_safety import ShellSafetyError, validate_shell_command
from hermes.tool_permissions import ToolPermissionError, enforce_tool_permission
from hermes.write_boundaries import WriteBoundaryError, ensure_within_write_boundary, validate_repo_changes
from scripts.contracts import validate_payload

SUPPORTED_TASK_TYPES = {"repo_summary", "text_generation", "file_write", "repo_write", "file_revert", "shell_command"}


class HermesExecutor:
    def __init__(self, workspace: Path, runner=None, memory_service: MemPalaceService | None = None):
        self.workspace = workspace
        self.runner = runner or DenyByDefaultRunner()
        self.memory_service = memory_service or MemPalaceService()
        self._dispatch = {
            "repo_summary": self._handle_repo_summary,
            "text_generation": self._handle_text_generation,
            "file_write": self._handle_file_write,
            "repo_write": self._handle_repo_write,
            "file_revert": self._handle_file_revert,
            "shell_command": self._handle_shell_command,
        }

    def execute(self, task_request: dict, preview_only: bool = False) -> dict:
        task = task_request.get("task", {})
        task_type = task.get("type")
        task_id = task.get("id") or "task_invalid"
        trace_id = task_request.get("trace", {}).get("trace_id") or f"trace_{task_id}"

        errors = validate_payload("task_request_v1.json", task_request)
        if errors:
            return self._failure(task_id, trace_id, "; ".join(errors), code="VALIDATION_FAILED")

        if task_type not in SUPPORTED_TASK_TYPES:
            return self._failure(task_id, trace_id, f"unsupported task type: {task_type}", code="VALIDATION_FAILED")

        try:
            enforce_tool_permission(task_request)
            memory_context = self._build_memory_context(task_request)
            with enforce_execution_runtime(max_runtime_seconds_for(task_request)):
                payload = self._dispatch[task_type](task_request, preview_only=preview_only)
                if memory_context is not None:
                    payload.setdefault("metadata", {})
                    payload["metadata"]["memory"] = memory_context
                    payload.setdefault("notes", []).append(f"Memory source: {memory_context.get('memory_source')}")
                enforce_output_size(payload, max_output_bytes_for(task_request))
            return self._success(task_id, trace_id, payload)
        except ToolPermissionError as exc:
            return self._failure(task_id, trace_id, str(exc), code="TOOL_PERMISSION_DENIED")
        except NetworkEgressDeniedError as exc:
            return self._failure(task_id, trace_id, str(exc), code="NETWORK_EGRESS_DENIED")
        except ShellSafetyError as exc:
            return self._failure(task_id, trace_id, str(exc), code="SHELL_SAFETY_DENIED")
        except SandboxDeniedError as exc:
            return self._failure(task_id, trace_id, str(exc), code="SANDBOX_DENIED")
        except ExecutionLimitError as exc:
            return self._failure(task_id, trace_id, str(exc), code="EXECUTION_LIMIT_EXCEEDED")
        except WriteBoundaryError as exc:
            return self._failure(task_id, trace_id, str(exc), code="WRITE_BOUNDARY_DENIED")
        except Exception as exc:
            return self._failure(task_id, trace_id, str(exc))

    def _memory_scope(self, task_request: dict) -> dict | None:
        tenant = task_request.get("task", {}).get("tenant") or {}
        tenant_id = str(tenant.get("tenant_id") or "").strip()
        if not tenant_id:
            return None
        return {
            "tenant_id": tenant_id,
            "org_id": str(tenant.get("org_id") or "").strip(),
            "client_id": str(tenant.get("client_id") or "").strip(),
        }

    def _build_memory_context(self, task_request: dict) -> dict | None:
        permissions = task_request.get("execution_policy", {}).get("permissions", {})
        if not permissions.get("allow_memory", False):
            return None
        scope = self._memory_scope(task_request)
        if scope is None:
            return None
        task = task_request.get("task", {})
        wakeup = self.memory_service.wakeup(scope, task.get("title", ""), task.get("description", ""))
        return {
            "tenant_id": scope["tenant_id"],
            "org_id": scope.get("org_id", ""),
            "client_id": scope.get("client_id", ""),
            "memory_mode": wakeup.get("memory_mode"),
            "memory_source": (wakeup.get("wakeup_context") or {}).get("memory_source"),
            "memory_hits": (wakeup.get("wakeup_context") or {}).get("memory_hits") or [],
            "fallback_reason": wakeup.get("fallback_reason"),
        }

    def _handle_repo_summary(self, task_request: dict, preview_only: bool = False) -> dict:
        labels = derive_action_labels("repo_summary", "allow", "scaffold", {"apply": False})
        return {
            "summary": "Repository summary scaffold result",
            "output": "# Repository Summary\n\nScaffold response generated.",
            "notes": [labels["operator_summary"]],
            "artifacts": [],
            "tool_calls": 0,
        }

    def _handle_text_generation(self, task_request: dict, preview_only: bool = False) -> dict:
        labels = derive_action_labels("text_generation", "allow", "scaffold", {"apply": False})
        return {
            "summary": "Text generation scaffold result",
            "output": "Generated scaffold text output.",
            "notes": [labels["operator_summary"]],
            "artifacts": [],
            "tool_calls": 0,
        }

    def _handle_file_write(self, task_request: dict, preview_only: bool = False) -> dict:
        context = task_request.get("task", {}).get("context", {})
        relative_path = context.get("file_path", "output.txt")
        ensure_within_write_boundary(self.workspace, relative_path)
        content = context.get("content", task_request.get("task", {}).get("description", ""))
        overwrite = bool(context.get("overwrite", False))
        if preview_only:
            previous = (self.workspace / relative_path).read_text() if (self.workspace / relative_path).exists() else ""
            preview = preview_change(previous, content)
            artifacts = [{"type": "file_preview", "path": relative_path, "content_type": "text/plain", "metadata": {"preview": preview}}]
            summary = f"Previewed file write for {relative_path}"
            notes = ["Preview only, no files changed"]
        else:
            result = write_workspace_file(self.workspace, relative_path, content, overwrite=overwrite)
            artifacts = [{"type": "file_write", "path": relative_path, "content_type": "text/plain", "metadata": {"bytes_written": result.bytes_written, "changed": result.changed}}]
            summary = f"Wrote file {relative_path}"
            notes = ["Applied file write in workspace"]
        return {
            "summary": summary,
            "output": summary,
            "notes": notes,
            "artifacts": artifacts,
            "tool_calls": 1,
        }

    def _handle_repo_write(self, task_request: dict, preview_only: bool = False) -> dict:
        changes = task_request.get("task", {}).get("context", {}).get("changes", [])
        validate_repo_changes(self.workspace, changes)
        result = preview_repo_write(self.workspace, changes) if preview_only else apply_repo_write(self.workspace, changes)
        artifacts = [
            {"type": "repo_write", "path": item.path, "content_type": "text/plain", "metadata": {"bytes_written": item.bytes_written, "changed": item.changed}}
            for item in result.files
        ]
        summary = f"{'Previewed' if preview_only else 'Applied'} repo write with {len(result.files)} file change(s)"
        notes = ["Preview only, no repo changes applied"] if preview_only else ["Applied repo write in workspace"]
        return {
            "summary": summary,
            "output": summary,
            "notes": notes,
            "artifacts": artifacts,
            "tool_calls": 1,
        }

    def _handle_file_revert(self, task_request: dict, preview_only: bool = False) -> dict:
        context = task_request.get("task", {}).get("context", {})
        relative_path = context.get("file_path", "output.txt")
        ensure_within_write_boundary(self.workspace, relative_path)
        previous_content = context.get("previous_content", "")
        result = revert_workspace_file(self.workspace, relative_path, previous_content)
        summary = f"Reverted file {relative_path}"
        return {
            "summary": summary,
            "output": summary,
            "notes": ["Reverted file change in workspace"],
            "artifacts": [{"type": "file_revert", "path": relative_path, "content_type": "text/plain", "metadata": {"restored": result.restored}}],
            "tool_calls": 1,
        }

    def _handle_shell_command(self, task_request: dict, preview_only: bool = False) -> dict:
        command = task_request.get("task", {}).get("context", {}).get("command") or task_request.get("task", {}).get("description", "")
        validate_shell_command(command)
        enforce_network_policy(task_request, command)
        max_runtime_seconds = max_runtime_seconds_for(task_request)
        result = self.runner.run(CommandRequest(command=command, cwd=self.workspace, max_runtime_seconds=max_runtime_seconds))
        return {
            "summary": f"Executed shell command: {command}",
            "output": f"Executed shell command: {command}",
            "notes": [f"Sandbox adapter returned: {result}"],
            "artifacts": [],
            "tool_calls": 1,
        }

    def _success(self, task_id: str, trace_id: str, payload: dict) -> dict:
        return {
            "schema_version": "v1",
            "task_id": task_id,
            "run": {
                "run_id": f"run_{task_id}",
                "status": "succeeded",
                "started_at": "2026-04-04T18:00:00Z",
                "finished_at": "2026-04-04T18:00:00Z",
                "runtime_seconds": 0,
            },
            "result": {
                "summary": payload["summary"],
                "output_format": "markdown",
                "output": payload["output"],
                "notes": payload["notes"],
                "metadata": payload.get("metadata", {}),
                "error": None,
            },
            "artifacts": payload["artifacts"],
            "usage": {
                "actual_cost_usd": 0.0,
                "model_provider": "local",
                "model_name": "scaffold",
                "tool_calls": payload["tool_calls"],
            },
            "trace": {
                "trace_id": trace_id,
                "reported_at": "2026-04-04T18:00:00Z",
            },
        }

    def _failure(self, task_id: str, trace_id: str, message: str, code: str = "EXECUTION_FAILED") -> dict:
        return {
            "schema_version": "v1",
            "task_id": task_id,
            "run": {
                "run_id": f"run_{task_id}",
                "status": "failed",
                "started_at": "2026-04-04T18:00:00Z",
                "finished_at": "2026-04-04T18:00:00Z",
                "runtime_seconds": 0,
            },
            "result": {
                "summary": "Task execution failed",
                "output_format": "markdown",
                "output": "",
                "notes": [],
                "error": {"code": code, "message": message, "retryable": False},
            },
            "artifacts": [],
            "usage": {
                "actual_cost_usd": 0.0,
                "model_provider": "local",
                "model_name": "scaffold",
                "tool_calls": 0,
            },
            "trace": {
                "trace_id": trace_id,
                "reported_at": "2026-04-04T18:00:00Z",
            },
        }
