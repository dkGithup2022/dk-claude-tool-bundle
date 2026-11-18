"""CODE 가 받음. 내용 없음 → 결과 없음 (build_output 에서 일을 함)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodeRequest:
    """CODE 가 받음. 내용 없음 → 결과 없음 (build_output 에서 일을 함)."""
