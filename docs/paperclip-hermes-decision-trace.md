# Paperclip ↔ Hermes Decision Trace

This document describes the first operator-facing decision-trace layer for Agentopia actions.

## What it adds

Recent Hermes result metadata now includes a `decision_trace` object describing:
- requested intent
- mapped task type
- policy mode / reason
- approval context
- target paths
- linked issue / run / agent ids
- compact decision summary

## Inspector

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_decision_traces.py
```

This lists recent runs carrying decision-trace metadata.

## Why this exists

Action labels and policy reasons explain outcomes, but decision trace adds the chain behind the action so operators can inspect why an agent did what it did.

## Current scope

This is an Agentopia-first inspection layer.
It is not yet a native Paperclip dashboard panel.

## Next step

After validating the traces on fresh runs, the next UI-facing step is to surface this data in a dedicated dashboard or issue-level panel.
