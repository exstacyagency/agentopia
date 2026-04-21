#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "memory_quality_cases.json"


def evaluate_case(case: dict) -> dict:
    scope = case["scope"]
    result = case["result"]
    expect = case["expect"]
    hits = result.get("results") or []
    tenant_id = scope["tenant_id"]
    all_hits_same_tenant = all(hit.get("tenant_id") == tenant_id for hit in hits)
    enough_hits = len(hits) >= expect.get("min_hits", 0)
    observed_good = bool(result.get("ok", False)) and all_hits_same_tenant and enough_hits
    expected_good = bool(expect.get("ok", False))
    passed = observed_good == expected_good
    return {
        "name": case["name"],
        "passed": passed,
        "expected_good": expected_good,
        "observed_good": observed_good,
        "tenant_isolation_ok": all_hits_same_tenant,
        "hit_count": len(hits),
        "reason": result.get("reason"),
    }


def main() -> int:
    cases = json.loads(FIXTURE.read_text())
    results = [evaluate_case(case) for case in cases]
    passed = sum(1 for item in results if item["passed"])
    summary = {
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
