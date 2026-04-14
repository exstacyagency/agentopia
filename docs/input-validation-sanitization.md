# Safer Input Validation and Sanitization

This document defines the minimum safer input validation and sanitization baseline for Agentopia in its current scaffold state.

## Goals

- reject obviously malformed string inputs early
- avoid persisting or executing control-character-heavy payloads
- keep sanitization behavior explicit and testable

## Current baseline

Before Paperclip or Hermes acts on request payloads, the repo should reject strings that contain unsafe control characters except for standard whitespace like newline, carriage return, and tab.

This baseline is intentionally narrow. It does not try to solve all prompt injection or business-logic misuse. It does provide a basic guardrail against malformed or binary-like payloads reaching deeper logic.

## Current rules

Reject request payloads containing string values with:

- null bytes
- other ASCII control characters below `0x20`
- except for:
  - tab
  - newline
  - carriage return

## Expected behavior

If invalid input is detected:

- return HTTP `400`
- return a JSON error describing the invalid input path
- do not continue into service or executor logic

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_input_validation.py
```

## Definition of done for this item

This repo can consider safer input validation and sanitization minimally defined when:

- request payload strings are recursively validated
- unsafe control-character input is rejected before deeper processing
- the behavior is documented and tested
