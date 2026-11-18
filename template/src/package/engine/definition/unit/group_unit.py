"""자식 단위 여러 개와 그것을 돌리는 방식."""

from __future__ import annotations

from dataclasses import dataclass

from package.engine.definition.ref import Ref
from package.engine.definition.unit.unit import Unit
from package.engine.runner.child_run.child_run import ChildRun


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupUnit(Unit):
    """자식 단위 여러 개와 그것을 돌리는 방식."""

    child_run: ChildRun
    children: tuple[Unit, ...]
    for_each_item_in: Ref | None = None  # ITEM_SOURCES 의 키와 인자. child_run 이 FOR_EACH_ITEM 일 때만

    def check(self) -> None:
        if not self.children:
            raise ValueError(f"{self.name}: 자식이 없다")
        if (self.child_run is ChildRun.FOR_EACH_ITEM) != (self.for_each_item_in is not None):
            raise ValueError(f"{self.name}: FOR_EACH_ITEM 이면 for_each_item_in 이 있어야 하고, 아니면 없어야 한다")
        names = [c.name for c in self.children]
        if len(names) != len(set(names)):
            raise ValueError(f"{self.name}: 자식 이름이 겹친다 {names}")
