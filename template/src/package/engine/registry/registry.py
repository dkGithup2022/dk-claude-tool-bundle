"""키 → 만드는 함수. 등록은 import 때 한 번, 쿼리는 명령마다."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from package.engine.definition.ref import Ref


class Registry[T](ABC):
    """키 → 만드는 함수. 등록은 import 때 한 번, 쿼리는 명령마다."""

    @abstractmethod
    def register(self, key: str, factory: Callable[..., T]) -> None:
        """같은 키가 이미 있으면 오류."""

    @abstractmethod
    def create(self, ref: Ref) -> T:
        """factory(**ref.args). 없는 키면 오류."""

    @abstractmethod
    def has(self, key: str) -> bool: ...

    @abstractmethod
    def factory_of(self, key: str) -> Callable[..., T]:
        """등록된 만드는 함수(작업이면 클래스). create 검사에서 request_type 을 읽을 때 쓴다."""

    def register_as[F: Callable[..., Any]](self, key: str) -> Callable[[F], F]:
        """데코레이터: 클래스나 함수 위에 붙여 등록한다."""

        def deco(factory: F) -> F:
            self.register(key, factory)
            return factory

        return deco
