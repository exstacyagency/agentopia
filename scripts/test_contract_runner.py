from __future__ import annotations

import json
from pathlib import Path

from contract_runner import ContractRunner
from output_models import HandoffPolicy, TaskOutput
from task_runner import TaskRunner


def make_runner() -> ContractRunner:
    return ContractRunner(Path('.'))


def make_task_runner() -> TaskRunner:
    return TaskRunner(Path('.'))


def test_validate_request_accepts_expected_shape():
    runner = make_runner()
    request = {
        "task": {
            "id": "task-123",
            "title": "Summarize repo changes",
            "priority": "medium",
            "requester": {"id": "human", "displayName": "human"},
            "budget": {"maxCostUsd": 5, "maxRuntimeMinutes": 15},
            "approval": {"required": False},
            "constraints": {
                "outputFormat": "markdown",
                "outputLength": "short",
                "allowNetwork": False,
            },
            "routing": {"inbound": "paperclip", "outbound": "hermes"},
        }
    }

    task = runner.validate_request(request)
    assert task["id"] == "task-123"


def test_validate_request_rejects_bad_routing():
    runner = make_runner()
    request = {
        "task": {
            "id": "task-123",
            "title": "Summarize repo changes",
            "priority": "medium",
            "requester": {"id": "human", "displayName": "human"},
            "budget": {"maxCostUsd": 5, "maxRuntimeMinutes": 15},
            "approval": {"required": False},
            "constraints": {
                "outputFormat": "markdown",
                "outputLength": "short",
                "allowNetwork": False,
            },
            "routing": {"inbound": "wrong", "outbound": "hermes"},
        }
    }

    try:
        runner.validate_request(request)
    except AssertionError as exc:
        assert "paperclip" in str(exc) or "routing" in str(exc)
    else:
        raise AssertionError("expected validation to fail")


def test_task_runner_writes_structured_output(tmp_path: Path):
    runner = make_task_runner()
    runner.root = tmp_path
    request = {
        "task": {
            "id": "task-999",
            "title": "Write summary",
            "priority": "low",
            "requester": {"id": "human", "displayName": "human"},
            "budget": {"maxCostUsd": 1, "maxRuntimeMinutes": 3},
            "approval": {"required": False},
            "constraints": {
                "outputFormat": "markdown",
                "outputLength": "short",
                "allowNetwork": False,
            },
            "routing": {"inbound": "paperclip", "outbound": "hermes"},
        }
    }
    runner.artifacts.mkdir(parents=True, exist_ok=True)
    runner.request_path.write_text(json.dumps(request))
    runner.run()
    output = json.loads((runner.artifacts / 'output.json').read_text())
    assert output['handoff']['from'] == 'paperclip'
    assert output['handoff']['to'] == 'hermes'
    assert output['handoff']['policy']['approvalRequired'] is False
    assert output['execution']['status'] == 'success'
    assert (runner.artifacts / 'summary.txt').read_text().startswith('Completed task: Write summary')
    assert output == json.loads((runner.fixture_path).read_text())


def test_output_models_are_constructible():
    output = TaskOutput(
        task_id='task-1',
        title='Task',
        priority='medium',
        policy=HandoffPolicy(5, 15, False),
        summary='Completed task: Task',
        notes=('a', 'b'),
    )
    assert output.policy.budget_usd == 5
    assert output.handoff_from == 'paperclip'
