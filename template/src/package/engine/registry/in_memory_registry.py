"""dict 하나로 두는 구현."""

from __future__ import annotations

from collections.abc import Callable

from package.engine.definition.ref import Ref
from package.engine.registry.registry import Registry


class InMemoryRegistry[T](Registry[T]):
    """dict 하나로 두는 구현."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._factories: dict[str, Callable[..., T]] = {}

    def register(self, key: str, factory: Callable[..., T]) -> None:
        if key in self._factories:
            raise ValueError(f"{self.kind} 키가 겹친다: {key}")
        self._factories[key] = factory

    def create(self, ref: Ref) -> T:
        return self.factory_of(ref.key)(**ref.args)

    def has(self, key: str) -> bool:
        return key in self._factories

    def factory_of(self, key: str) -> Callable[..., T]:
        factory = self._factories.get(key)
        if factory is None:
            raise KeyError(f"등록되지 않은 {self.kind}: {key}")
        return factory
