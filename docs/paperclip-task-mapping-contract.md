# Paperclip → Hermes Task Mapping Contract

This document defines the Agentopia-side contract for turning Paperclip issue content into an Agentopia Hermes v1 task request.

## Source of truth

The source of truth for this mapping lives in Agentopia:
- `hermes/paperclip_mapping.py`
- `hermes/paperclip_bridge.py`

Paperclip local patches should mirror this behavior, not invent a separate routing policy.

## Current routing rules

### file_analysis
Route to `file_analysis` when issue text suggests a concrete file/path-oriented task.

Examples:
- explicit file paths like `docs/README.md`
- phrases like `analyze file`, `inspect file`, `read file`
- common source/doc file extensions

### text_generation
Route to `text_generation` when issue text is drafting-oriented.

Examples:
- `write`
- `draft`
- `generate`
- `compose`
- `announcement`
- `email`
- `message`
- `post`

### repo_summary
Route to `repo_summary` when issue text is repo/codebase overview oriented, or when no stronger rule matches.

Examples:
- `repo`
- `repository`
- `codebase`
- `overview`
- `summarize repository`

## Output envelope

The bridge builder produces a valid Agentopia v1 task request with:
- mapped `task.type`
- mapped `task.context`
- `issue_id`
- `paperclip_run_id`
- `agent_id`
- routing callback
- trace metadata

## Why this exists

This keeps routing policy and task-envelope construction in Agentopia, which is the repo of record for the integration.
