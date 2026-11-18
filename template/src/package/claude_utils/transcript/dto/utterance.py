"""대화 기록의 말 하나."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Utterance:
    id: str  # 사용자 u1.., Claude a1..
    role: str  # user | assistant
    text: str
    at: str
