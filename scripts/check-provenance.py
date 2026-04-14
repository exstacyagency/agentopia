#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCKFILE = ROOT / "requirements.lock"
PRODUCTION_ENV = ROOT / "config" / "environments" / "production.env"


def check_lockfile() -> list[str]:
    issues: list[str] = []
    for line_no, raw in enumerate(LOCKFILE.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            issues.append(f"requirements.lock:{line_no}: comments are not allowed")
            continue
        if "==" not in line:
            issues.append(f"requirements.lock:{line_no}: dependency must use exact == pin")
            continue
        if any(token in line for token in (" @ ", "-e ", "git+", "file:")):
            issues.append(f"requirements.lock:{line_no}: non-index or editable dependency source is not allowed")
    return issues


def check_production_images() -> list[str]:
    issues: list[str] = []
    for line_no, raw in enumerate(PRODUCTION_ENV.read_text().splitlines(), start=1):
        line = raw.strip()
        if line.startswith("PAPERCLIP_IMAGE=") or line.startswith("HERMES_IMAGE="):
            _, value = line.split("=", 1)
            if "@sha256:" not in value:
                issues.append(f"production.env:{line_no}: production image ref must be digest-pinned")
    return issues


def main() -> int:
    issues = [*check_lockfile(), *check_production_images()]
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("provenance checks ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
