#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required; install it in your environment") from exc

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validator_for(schema_name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS / schema_name)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_payload(schema_name: str, payload: dict) -> list[str]:
    validator = validator_for(schema_name)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    messages: list[str] = []
    for err in errors:
        path = ".".join(str(part) for part in err.absolute_path) or "<root>"
        messages.append(f"{path}: {err.message}")
    return messages


def assert_valid(schema_name: str, payload: dict) -> None:
    errors = validate_payload(schema_name, payload)
    if errors:
        raise AssertionError("\n".join(errors))
