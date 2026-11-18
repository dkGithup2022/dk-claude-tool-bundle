"""<노드 폴더>/result.json. 항목 번호 → 결과. 반복 밖이면 키 NO_ITEM_KEY("-") 하나."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class NodeResult:
    """<노드 폴더>/result.json. 항목 번호 → 결과. 반복 밖이면 키 NO_ITEM_KEY("-") 하나."""

    by_item: dict[str, dict[str, Any]]
