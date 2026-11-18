"""묶음 단위가 자식 단위를 어떻게 돌리는가."""

from __future__ import annotations

from enum import StrEnum


class ChildRun(StrEnum):
    """묶음 단위가 자식 단위를 어떻게 돌리는가."""

    IN_ORDER = "in_order"  # 차례로
    FOR_EACH_ITEM = "for_each_item"  # 항목마다 같은 자식들을
