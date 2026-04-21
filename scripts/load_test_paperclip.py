#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scripts.paperclip_client_helper import PaperclipClient

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "task_request_valid.json"


def run_one(client: PaperclipClient, base_payload: dict, index: int, timeout_seconds: int) -> dict:
    payload = json.loads(json.dumps(base_payload))
    payload["task"]["id"] = f"load_task_{index}"
    payload["trace"]["trace_id"] = f"trace_load_{index}"
    started = time.perf_counter()
    status, created = client.submit_task(payload, idempotency_key=f"load-{index}")
    if status != 201:
        return {"ok": False, "status": status, "latency_seconds": time.perf_counter() - started}
    task_id = created["id"]
    wait_status, task = client.wait_for_terminal_state(task_id, timeout_seconds=timeout_seconds, poll_interval_seconds=0.2)
    ended = time.perf_counter()
    return {
        "ok": wait_status == 200 and task.get("state") == "succeeded",
        "status": wait_status,
        "latency_seconds": ended - started,
        "task_id": task_id,
        "state": task.get("state") if isinstance(task, dict) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a lightweight Paperclip load baseline")
    parser.add_argument("--base-url", default="http://127.0.0.1:3100")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=15)
    args = parser.parse_args()

    payload = json.loads(FIXTURE.read_text())
    client = PaperclipClient(args.base_url, args.api_key)

    started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(run_one, client, payload, i, args.timeout_seconds) for i in range(args.requests)]
        for future in as_completed(futures):
            results.append(future.result())
    total_seconds = time.perf_counter() - started

    latencies = [item["latency_seconds"] for item in results]
    ok_count = sum(1 for item in results if item["ok"])
    summary = {
        "requests": args.requests,
        "concurrency": args.concurrency,
        "ok_count": ok_count,
        "error_count": args.requests - ok_count,
        "total_seconds": total_seconds,
        "throughput_rps": (args.requests / total_seconds) if total_seconds else 0.0,
        "latency_seconds": {
            "min": min(latencies) if latencies else None,
            "p50": statistics.median(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if ok_count == args.requests else 1


if __name__ == "__main__":
    raise SystemExit(main())
