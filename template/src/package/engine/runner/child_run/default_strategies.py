"""default_strategies: 자식 실행 방식 2개를 ChildRun 별로 묶는다."""

from __future__ import annotations

from package.engine.runner.child_run.child_run import ChildRun
from package.engine.runner.child_run.child_run_strategy import ChildRunStrategy
from package.engine.runner.child_run.for_each_item_strategy import ForEachItemStrategy
from package.engine.runner.child_run.in_order_strategy import InOrderStrategy


def default_strategies() -> dict[ChildRun, ChildRunStrategy]:
    return {s.child_run: s for s in (InOrderStrategy(), ForEachItemStrategy())}
