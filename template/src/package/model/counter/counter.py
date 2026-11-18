"""카운터. 실행할 때마다 1씩 늘어 파일에 남는 값 (count_joke 예시의 도메인 데이터)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Counter:
    value: int

    def up(self) -> Counter:
        """1 늘린 새 Counter. 자신은 바꾸지 않는다."""
        return Counter(self.value + 1)
