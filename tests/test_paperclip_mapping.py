from hermes.paperclip_mapping import map_paperclip_issue_to_task


def test_maps_file_analysis_from_path_hint() -> None:
    mapped = map_paperclip_issue_to_task(
        "Inspect README",
        "Please analyze docs/README.md and explain what is missing.",
    )
    assert mapped.task_type == "file_analysis"
    assert mapped.context["file_path"] == "docs/README.md"


def test_maps_text_generation_from_draft_hint() -> None:
    mapped = map_paperclip_issue_to_task(
        "Draft announcement",
        "Write a short release announcement for the new executor bridge.",
    )
    assert mapped.task_type == "text_generation"
    assert "release announcement" in mapped.context["prompt"]


def test_maps_repo_summary_from_repo_hint() -> None:
    mapped = map_paperclip_issue_to_task(
        "Repository overview",
        "Give me a repo overview and summarize the codebase.",
        fallback_repo="repo-agentopia",
    )
    assert mapped.task_type == "repo_summary"
    assert mapped.context["repo"] == "repo-agentopia"


def test_maps_structured_extract_from_extract_hint() -> None:
    mapped = map_paperclip_issue_to_task(
        "Extract setup steps",
        "Extract the setup steps from docs/README.md into a checklist.",
        fallback_repo="repo-agentopia",
    )
    assert mapped.task_type == "structured_extract"
    assert mapped.context["source"] == "docs/README.md"


def test_maps_repo_change_plan_from_plan_hint() -> None:
    mapped = map_paperclip_issue_to_task(
        "Plan the changes for approval routing",
        "Plan the implementation, impacted files, and acceptance checks for Hermes approval routing.",
        fallback_repo="repo-agentopia",
    )
    assert mapped.task_type == "repo_change_plan"
    assert mapped.context["repo"] == "repo-agentopia"
