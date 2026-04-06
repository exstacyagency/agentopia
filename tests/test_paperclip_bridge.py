from hermes.paperclip_bridge import build_paperclip_task_request


def test_bridge_builds_file_analysis_request() -> None:
    task = build_paperclip_task_request(
        issue_id="ISS-1",
        issue_title="Inspect README",
        issue_description="Please analyze docs/README.md and explain what is missing.",
        paperclip_run_id="run-123",
        agent_id="agent-1",
        fallback_repo="repo-agentopia",
    )
    assert task["task"]["type"] == "file_analysis"
    assert task["task"]["context"]["file_path"] == "docs/README.md"
    assert task["task"]["context"]["paperclip_run_id"] == "run-123"


def test_bridge_builds_text_generation_request() -> None:
    task = build_paperclip_task_request(
        issue_id="ISS-2",
        issue_title="Draft announcement",
        issue_description="Write a short release announcement for the new executor bridge.",
        paperclip_run_id="run-456",
        agent_id="agent-2",
    )
    assert task["task"]["type"] == "text_generation"
    assert "announcement" in task["task"]["context"]["prompt"]


def test_bridge_builds_repo_summary_request() -> None:
    task = build_paperclip_task_request(
        issue_id="ISS-3",
        issue_title="Repository overview",
        issue_description="Give me a repo overview and summarize the codebase.",
        paperclip_run_id="run-789",
        agent_id="agent-3",
        fallback_repo="repo-agentopia",
    )
    assert task["task"]["type"] == "repo_summary"
    assert task["task"]["context"]["repo"] == "repo-agentopia"
