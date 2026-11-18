"""ClaudeCliError."""

from __future__ import annotations


class ClaudeCliError(RuntimeError):
    """claude -p 가 실패함 (종료 코드, 시간 초과, 출력 형식)."""
