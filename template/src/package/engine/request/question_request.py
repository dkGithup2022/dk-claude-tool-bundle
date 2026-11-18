"""MAIN_SESSION_ASK 가 받음 → 결과: 답 str."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionRequest:
    """MAIN_SESSION_ASK 가 받음 → 결과: 답 str."""

    question: str
    choices: tuple[str, ...]
