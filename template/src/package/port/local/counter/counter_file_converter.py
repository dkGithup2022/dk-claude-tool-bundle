"""CounterFileConverter: Counter ↔ counter.json."""

from __future__ import annotations

from typing import Any

from package.model.counter.counter import Counter


class CounterFileConverter:
    def to_file(self, c: Counter) -> dict[str, Any]:
        return {"value": c.value}

    def to_data(self, d: dict[str, Any]) -> Counter:
        return Counter(int(d["value"]))
