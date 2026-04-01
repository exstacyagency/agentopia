from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestSchema:
    task_id: str
    title: str
    priority: str
    requester_id: str
    requester_display_name: str
    max_cost_usd: int
    max_runtime_minutes: int
    approval_required: bool
    output_format: str
    output_length: str
    allow_network: bool
    inbound: str
    outbound: str


@dataclass(frozen=True)
class ResultSchema:
    task_id: str
    status: str
    summary: str
    artifacts: tuple[str, ...]
    approved_by: str
    executed_by: str
    runtime_seconds: int
