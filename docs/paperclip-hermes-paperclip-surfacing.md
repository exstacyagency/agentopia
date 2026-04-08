# Paperclip ↔ Hermes Paperclip Surfacing Plan

This document describes the Paperclip-visible surfacing path for Hermes execution summaries.

## Implemented step

Agentopia now has:
- a comment-body builder in `paperclip_adapter/comments.py`
- a service helper in `paperclip_adapter/service.py` for posting execution summaries back to Paperclip issues
- a client helper in `paperclip_adapter/http_client.py` for issue comments

## Comment content

Structured issue comments can summarize:
- action label
- action category
- action reason
- operator summary
- policy mode / reason
- approval id / status when present

## Why comments first

Comments are the lightest first surfacing path that makes the semantic labels visible in the Paperclip UI without requiring immediate Paperclip schema or UI changes.

## Next validation step

Post a structured summary comment to a real Paperclip issue and confirm it appears in the issue timeline.
