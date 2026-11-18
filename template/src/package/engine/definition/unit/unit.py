"""모든 작업 단위의 공통 부분. 만들 때 검사는 여기서 한 번에 한다."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from package.engine.definition.ref import Ref

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True, slots=True, kw_only=True)
class Unit(ABC):
    """모든 작업 단위의 공통 부분. 만들 때 검사는 여기서 한 번에 한다."""

    name: str  # = 노드 폴더 이름 앞부분. 영문 소문자·숫자·_
    run_if: Ref | None = None  # CONDITIONS 의 키와 인자
    reads: tuple[str, ...] = ()  # 이 단위(Task·반복 항목 함수·조건)가 결과를 읽는 앞 노드의 이름

    def __post_init__(self) -> None:
        if not _NAME.match(self.name):
            raise ValueError(f"단위 이름은 영문 소문자·숫자·_ (노드 폴더 이름이 됨): {self.name!r}")
        self.check()

    @abstractmethod
    def check(self) -> None:
        """이 종류의 단위만의 검사. 어기면 ValueError. 하위 클래스는 __post_init__ 을 다시 정의하지 않는다."""
