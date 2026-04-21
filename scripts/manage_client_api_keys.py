#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path


def load_registry(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"keys": []}


def save_registry(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def issue_key(args) -> int:
    payload = load_registry(args.registry)
    raw_key = secrets.token_urlsafe(24)
    payload.setdefault("keys", []).append(
        {
            "id": args.key_id,
            "role": args.role,
            "tenant_id": args.tenant_id,
            "org_id": args.org_id,
            "client_id": args.client_id,
            "key": raw_key,
            "status": "active",
        }
    )
    save_registry(args.registry, payload)
    print(json.dumps({"id": args.key_id, "key": raw_key, "registry": str(args.registry)}, indent=2))
    return 0


def revoke_key(args) -> int:
    payload = load_registry(args.registry)
    for item in payload.get("keys", []):
        if item.get("id") == args.key_id:
            item["status"] = "revoked"
            save_registry(args.registry, payload)
            print(json.dumps({"id": args.key_id, "status": "revoked"}, indent=2))
            return 0
    raise SystemExit(f"key id not found: {args.key_id}")


def rotate_key(args) -> int:
    payload = load_registry(args.registry)
    for item in payload.get("keys", []):
        if item.get("id") == args.key_id:
            item["status"] = "revoked"
            new_key = secrets.token_urlsafe(24)
            replacement = dict(item)
            replacement["id"] = args.new_key_id or f"{args.key_id}_rotated"
            replacement["key"] = new_key
            replacement["status"] = "active"
            payload["keys"].append(replacement)
            save_registry(args.registry, payload)
            print(json.dumps({"revoked": args.key_id, "new_id": replacement["id"], "key": new_key}, indent=2))
            return 0
    raise SystemExit(f"key id not found: {args.key_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage file-based Paperclip client API keys")
    parser.add_argument("--registry", type=Path, default=Path("config/paperclip/client_api_keys.json"))
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue")
    issue.add_argument("--key-id", required=True)
    issue.add_argument("--role", default="submitter")
    issue.add_argument("--tenant-id", required=True)
    issue.add_argument("--org-id", default="")
    issue.add_argument("--client-id", default="")
    issue.set_defaults(func=issue_key)

    revoke = sub.add_parser("revoke")
    revoke.add_argument("--key-id", required=True)
    revoke.set_defaults(func=revoke_key)

    rotate = sub.add_parser("rotate")
    rotate.add_argument("--key-id", required=True)
    rotate.add_argument("--new-key-id")
    rotate.set_defaults(func=rotate_key)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
