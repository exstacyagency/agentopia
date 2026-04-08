# Paperclip ↔ Hermes Paperclip Surfacing Plan

This document describes the next layer after Hermes-side semantic labeling: surfacing those labels back into Paperclip-visible issue history.

## Problem

The semantic fields now exist in Hermes result metadata and Agentopia operator summaries, but they are not yet visible in the Paperclip UI.

## Proposed first step

Post a structured issue comment back into Paperclip after execution for runs that have:
- `paperclip_issue_id`
- semantic action label metadata

## Suggested comment content

A Paperclip issue comment can summarize:
- action label
- action category
- action reason
- operator summary
- policy mode / reason
- approval id / status when present

## Why comments first

Comments are a lightweight, user-visible surfacing path that does not require immediate Paperclip schema/UI changes.

## Initial implementation surface

Agentopia now has a client helper for:
- `create_issue_comment(company_id, issue_id, body)`

The next implementation step would be:
1. build a structured execution summary comment body
2. post it to the relevant Paperclip issue after successful execution or meaningful policy block
3. validate that the comment is visible in the Paperclip issue timeline
