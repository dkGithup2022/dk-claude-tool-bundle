"""작업 하나를 누가 수행하는가."""

from __future__ import annotations

from enum import StrEnum


class PerformedBy(StrEnum):
    """작업 하나를 누가 수행하는가."""

    CODE = "code"  # 코드가 바로 수행
    CLAUDE_P = "claude_p"  # claude -p 가 판단
    MAIN_SESSION_SHOW = "main_session_show"  # 메인 세션이 글을 보여 줌. 답을 기다리지 않음
    MAIN_SESSION_ASK = "main_session_ask"  # 메인 세션이 선택지로 물음
    MAIN_SESSION_TALK = "main_session_talk"  # 메인 세션이 대화
    SUBAGENT = "subagent"  # 메인 세션이 서브에이전트를 띄움
