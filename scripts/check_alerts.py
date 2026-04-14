#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from urllib.error import HTTPError, URLError

PAPERCLIP_URL = "http://127.0.0.1:3100"
HERMES_URL = "http://127.0.0.1:3200"


def fetch_json(url: str) -> tuple[int, dict | None]:
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode()
        return exc.code, json.loads(body) if body else None
    except URLError:
        return 0, None


def fetch_text(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.read().decode()
    except HTTPError as exc:
        return exc.code, exc.read().decode()
    except URLError:
        return 0, ""


def evaluate_alerts(paperclip_base: str = PAPERCLIP_URL, hermes_base: str = HERMES_URL) -> list[str]:
    alerts: list[str] = []

    for service, base in (("paperclip", paperclip_base), ("hermes", hermes_base)):
        status, payload = fetch_json(f"{base}/health")
        if status != 200 or not payload or not payload.get("ok"):
            alerts.append(f"{service}: health endpoint unhealthy")

        _, metrics = fetch_text(f"{base}/metrics")
        if "requests_rejected_total" in metrics:
            for line in metrics.splitlines():
                if line.endswith("_requests_rejected_total 0"):
                    continue
                if "_requests_rejected_total" in line:
                    alerts.append(f"{service}: rejected request counter non-zero")
                    break

    return alerts


def main() -> int:
    alerts = evaluate_alerts()
    if alerts:
        for alert in alerts:
            print(alert)
        return 1
    print("no alerts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
