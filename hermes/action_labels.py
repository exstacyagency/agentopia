from __future__ import annotations


def derive_action_labels(task_type: str, policy_mode: str, policy_reason: str, context: dict) -> dict:
    preview_only = bool((context or {}).get("apply") is False)

    if task_type == "file_analysis":
        return {
            "action_label": "file_analysis",
            "action_category": "analysis",
            "action_reason": "issue requested file-focused analysis based on the mapped Paperclip prompt",
            "operator_summary": "Analyze a referenced file and return findings",
            "issue_origin": "mapped_from_issue_prompt",
        }

    if task_type == "repo_change_plan":
        return {
            "action_label": "repo_change_plan",
            "action_category": "planning",
            "action_reason": "issue was interpreted as a repository planning request",
            "operator_summary": "Produce a repository change plan",
            "issue_origin": "mapped_from_issue_prompt",
        }

    if task_type == "implementation_draft":
        return {
            "action_label": "implementation_draft",
            "action_category": "drafting",
            "action_reason": "issue was interpreted as an implementation drafting request",
            "operator_summary": "Draft implementation details without applying changes",
            "issue_origin": "mapped_from_issue_prompt",
        }

    if task_type == "file_write":
        if policy_mode == "deny":
            return {
                "action_label": "blocked_file_write",
                "action_category": "blocked_write",
                "action_reason": f"file write was blocked because policy reason was {policy_reason}",
                "operator_summary": "Blocked file write request",
                "issue_origin": "approval_linked_write_request",
            }
        return {
            "action_label": "approved_file_write",
            "action_category": "approved_write",
            "action_reason": f"file write was produced because an approval-linked write request satisfied policy reason {policy_reason}",
            "operator_summary": "Approved workspace-scoped file write",
            "issue_origin": "approval_linked_write_request",
        }

    if task_type == "repo_write":
        if preview_only or policy_mode == "preview":
            return {
                "action_label": "preview_repo_write",
                "action_category": "preview_write",
                "action_reason": "repo write was produced in preview mode because apply=false requested a non-applied change preview",
                "operator_summary": "Preview constrained repository changes without applying them",
                "issue_origin": "approval_linked_repo_write_request",
            }
        if policy_mode == "deny":
            return {
                "action_label": "blocked_repo_write",
                "action_category": "blocked_write",
                "action_reason": f"repo write was blocked because policy reason was {policy_reason}",
                "operator_summary": "Blocked constrained repository write",
                "issue_origin": "approval_linked_repo_write_request",
            }
        return {
            "action_label": "approved_repo_write",
            "action_category": "approved_write",
            "action_reason": f"repo write was produced because an approval-linked repository change request satisfied policy reason {policy_reason}",
            "operator_summary": "Apply constrained repository changes",
            "issue_origin": "approval_linked_repo_write_request",
        }

    if task_type == "file_revert":
        if policy_mode == "deny":
            return {
                "action_label": "blocked_file_revert",
                "action_category": "blocked_revert",
                "action_reason": f"file revert was blocked because policy reason was {policy_reason}",
                "operator_summary": "Blocked workspace-scoped file revert",
                "issue_origin": "rollback_request",
            }
        return {
            "action_label": "approved_file_revert",
            "action_category": "approved_revert",
            "action_reason": f"file revert was performed because an approval-linked rollback request satisfied policy reason {policy_reason}",
            "operator_summary": "Restore a workspace-scoped file to prior content",
            "issue_origin": "rollback_request",
        }

    return {
        "action_label": task_type,
        "action_category": "general",
        "action_reason": "action was produced from the mapped Paperclip issue and task type",
        "operator_summary": task_type,
        "issue_origin": "mapped_from_issue_prompt",
    }
