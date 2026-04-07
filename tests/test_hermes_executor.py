from pathlib import Path

from hermes.executor import HermesExecutor


def build_payload(task_type: str, context: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "task": {
            "id": f"task-{task_type}",
            "type": task_type,
            "title": f"Test {task_type}",
            "description": f"Exercise {task_type}",
            "priority": "medium",
            "risk_level": "low",
            "requester": {"id": "tester", "display_name": "Tester"},
            "context": context or {},
            "created_at": "2026-04-06T19:50:00Z",
        },
        "execution_policy": {
            "budget": {"max_cost_usd": 5.0, "max_runtime_minutes": 10},
            "approval": {"required": False, "status": "not_required"},
            "permissions": {
                "allow_network": False,
                "allow_memory": False,
                "allow_tools": False,
                "allowed_tool_classes": [],
                "write_scope": "none",
            },
            "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": True},
        },
        "routing": {
            "source": "paperclip",
            "destination": "hermes",
            "callback": {"result_url": "http://127.0.0.1/result", "auth_mode": "shared_token"},
        },
        "trace": {"trace_id": f"trace-{task_type}", "submitted_at": "2026-04-06T19:50:00Z"},
    }


def test_repo_summary_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("repo_summary", {"repo": "repo-agentopia", "branch": "main"}))
    assert result["run"]["status"] == "succeeded"
    assert "# Repo Summary" in result["result"]["output"]


def test_file_analysis_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("file_analysis", {"file_path": "README.md", "objective": "Inspect docs"}))
    assert result["run"]["status"] == "succeeded"
    assert "# File Analysis" in result["result"]["output"]
    assert "README.md" in result["result"]["output"]


def test_text_generation_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("text_generation", {"prompt": "Draft release note", "tone": "concise"}))
    assert result["run"]["status"] == "succeeded"
    assert "# Text Generation" in result["result"]["output"]
    assert "Draft release note" in result["result"]["output"]


def test_result_metadata_contains_bridge_fields() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("text_generation", {
        "prompt": "Draft release note",
        "tone": "concise",
        "issue_id": "ISS-9",
        "paperclip_run_id": "run-999",
        "agent_id": "agent-9",
    }))
    metadata = result["result"]["metadata"]
    assert metadata["task_type"] == "text_generation"
    assert metadata["paperclip_issue_id"] == "ISS-9"
    assert metadata["paperclip_run_id"] == "run-999"
    assert metadata["agent_id"] == "agent-9"


def test_structured_extract_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("structured_extract", {"source": "docs/README.md", "extraction_goal": "Extract setup steps"}))
    assert result["run"]["status"] == "succeeded"
    assert "# Structured Extract" in result["result"]["output"]
    assert result["result"]["metadata"]["task_type"] == "structured_extract"


def test_repo_change_plan_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("repo_change_plan", {"repo": "repo-agentopia", "goal": "Plan approval routing"}))
    assert result["run"]["status"] == "succeeded"
    assert "# Repo Change Plan" in result["result"]["output"]
    assert result["result"]["metadata"]["task_type"] == "repo_change_plan"


def test_implementation_draft_supported() -> None:
    executor = HermesExecutor(Path.cwd())
    result = executor.execute(build_payload("implementation_draft", {"goal": "Draft approval routing", "impacted_files": ["service.py"]}))
    assert result["run"]["status"] == "succeeded"
    assert "# Implementation Draft" in result["result"]["output"]
    assert result["result"]["metadata"]["task_type"] == "implementation_draft"
