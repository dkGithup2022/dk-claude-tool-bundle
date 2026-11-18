"""MAIN_SESSION_SHOW 가 받음 → 결과 없음 (보이자마자 끝)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShowRequest:
    """MAIN_SESSION_SHOW 가 받음 → 결과 없음 (보이자마자 끝)."""

    text: str
