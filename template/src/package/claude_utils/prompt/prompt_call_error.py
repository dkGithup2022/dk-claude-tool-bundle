"""PromptCallError: claude -p 호출 실패. 호출 기록 전체를 담는다."""

from __future__ import annotations

from package.claude_utils.prompt.claude_cli_error import ClaudeCliError
from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord


class PromptCallError(ClaudeCliError):
    """claude -p 호출 실패. 실패한 호출의 기록 전체를 담는다 (비용·시간을 남기려고)."""

    def __init__(self, message: str, record: PromptCallRecord) -> None:
        super().__init__(message)
        self.record = record
