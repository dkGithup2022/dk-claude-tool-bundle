"""MAIN_SESSION_TALK 가 받음 → 결과: 대화 구간."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConversationRequest:
    """MAIN_SESSION_TALK 가 받음 → 결과: 대화 구간."""

    goal: str
    opening: str
