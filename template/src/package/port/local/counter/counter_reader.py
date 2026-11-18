"""CounterReader: 카운터 읽기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.model.counter.counter import Counter


class CounterReader(ABC):
    @abstractmethod
    def read(self) -> Counter:
        """저장된 카운터. 없으면 0."""
