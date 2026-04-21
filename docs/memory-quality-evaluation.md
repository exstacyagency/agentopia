# Memory Quality Evaluation

This document defines the current memory quality evaluation baseline.

## Goal

Provide a reproducible baseline for evaluating whether memory behavior is:

- tenant-safe
- plausibly relevant
- explicit about fallback and degraded behavior

## Current baseline

The current evaluation harness uses fixture-driven cases in:

- `fixtures/memory_quality_cases.json`

And evaluates them with:

- `scripts/evaluate_memory_quality.py`

## What it checks today

The current baseline checks:

- whether returned hits stay within the requesting tenant boundary
- whether relevant cases produce at least a minimum number of hits
- whether fallback/degraded cases are surfaced as such

## Example run

```bash
./.venv/bin/python scripts/evaluate_memory_quality.py
```

## Notes

This is a baseline evaluator, not a full memory benchmark suite.
It gives the repo a reproducible way to judge obvious memory quality regressions, especially around tenant isolation and fallback behavior.

## Verification

Run:

```bash
./.venv/bin/python scripts/test_memory_quality_evaluation.py
```
