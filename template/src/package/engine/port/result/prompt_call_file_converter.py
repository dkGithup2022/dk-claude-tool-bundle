"""PromptCallFileConverter: PromptCallRecord ↔ <노드 폴더>/calls/<n>/request.json, response.json."""

from __future__ import annotations

from typing import Any

from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord


class PromptCallFileConverter:
    def to_file(self, r: PromptCallRecord) -> tuple[dict[str, Any], dict[str, Any]]:
        """(request.json 내용, response.json 내용)."""
        return dict(r.request), dict(r.response)

    def to_data(self, request: dict[str, Any], response: dict[str, Any]) -> PromptCallRecord:
        return PromptCallRecord(dict(request), dict(response))
