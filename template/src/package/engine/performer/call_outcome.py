"""CLAUDE_P 수행 결과: 값과 호출 기록 위치·비용·시간. 실행기가 history 에 옮긴다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CallOutcome:
    """CLAUDE_P 수행 결과: 값과 호출 기록 위치·비용·시간. 실행기가 history 에 옮긴다."""

    value: Any
    call_file: str
    cost_usd: float | None
    seconds: float | None
