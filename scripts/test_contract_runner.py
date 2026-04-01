from __future__ import annotations

import json
from pathlib import Path

from scripts.contract_runner import validate_request


def test_validate_request_accepts_expected_shape():
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

    task = validate_request(request)
    assert task["id"] == "task-123"


def test_validate_request_rejects_bad_routing():
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
        validate_request(request)
    except AssertionError as exc:
        assert "paperclip" in str(exc) or "routing" in str(exc)
    else:
        raise AssertionError("expected validation to fail")
