from __future__ import annotations

import os
from typing import Any

from hermes.paperclip_dashboard import build_issue_dashboard_document
from paperclip_adapter.comments import build_execution_summary_comment
from paperclip_adapter.http_client import PaperclipClientConfig, PaperclipHttpClient


class PaperclipCommentPoster:
    def __init__(self) -> None:
        base_url = os.environ.get("PAPERCLIP_BASE_URL", "http://127.0.0.1:3100")
        self.client = PaperclipHttpClient(PaperclipClientConfig(base_url=base_url))

    def post_execution_summary(self, issue_id: str, result: dict[str, Any]) -> dict[str, Any]:
        comment = build_execution_summary_comment(result)
        return self.client.create_issue_comment(issue_id, comment["body"])

    def publish_issue_dashboard(self, issue_id: str, result: dict[str, Any]) -> dict[str, Any]:
        document = build_issue_dashboard_document(result)
        return self.client.upsert_issue_document(issue_id, document["key"], document["title"], document["body"])
