#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITIGNORE = ROOT / ".gitignore"

REQUIRED_GITIGNORE_LINES = {
    "config/environments/*.secrets.env",
    "config/environments/*.rendered.env",
}

FORBIDDEN_TRACKED_SECRET_PATTERNS = (
    "production-real-",
    "live-",
    "sk_live_",
    "ghp_",
    "Bearer ",
)

SCAN_FILES = [
    ROOT / ".env.example",
    ROOT / "config" / "environments" / "development.env",
    ROOT / "config" / "environments" / "staging.env",
    ROOT / "config" / "environments" / "production.env",
]


def main() -> int:
    issues: list[str] = []

    gitignore_lines = set(GITIGNORE.read_text().splitlines())
    for required in REQUIRED_GITIGNORE_LINES:
        if required not in gitignore_lines:
            issues.append(f"missing gitignore rule: {required}")

    for path in SCAN_FILES:
        text = path.read_text()
        for pattern in FORBIDDEN_TRACKED_SECRET_PATTERNS:
            if pattern in text:
                issues.append(f"{path.relative_to(ROOT)} contains forbidden secret-like pattern: {pattern}")

    if issues:
        for issue in issues:
            print(issue)
        return 1

    print("secret handling checks ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
