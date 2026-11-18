"""<반복 노드 폴더>/items.json. 처음 한 번 고정한 반복 항목."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FixedItems:
    """<반복 노드 폴더>/items.json. 처음 한 번 고정한 반복 항목."""

    items: tuple[Any, ...]
    fixed_at: str
