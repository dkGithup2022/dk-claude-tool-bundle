"""make_joke 프롬프트의 출력 모양. 필드 이름이 claude -p 출력 JSON 의 키가 된다."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MakeJokeOutput:
    joke: str  # 숫자를 이용한 말장난 한 문장
