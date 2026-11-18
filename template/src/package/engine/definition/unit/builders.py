"""task(), group(): 작업 단위를 짧게 만드는 함수. 검사는 생성자가 한다."""

from __future__ import annotations

from package.engine.definition.ref import Ref
from package.engine.definition.unit.group_unit import GroupUnit
from package.engine.definition.unit.task_unit import TaskUnit
from package.engine.definition.unit.unit import Unit
from package.engine.performer.performed_by import PerformedBy
from package.engine.runner.child_run.child_run import ChildRun


def task(
    name: str, performed_by: PerformedBy, task: Ref, run_if: Ref | None = None, reads: tuple[str, ...] = ()
) -> TaskUnit:
    """TaskUnit 을 짧게 만든다. 검사는 생성자가 한다."""
    return TaskUnit(name=name, performed_by=performed_by, task=task, run_if=run_if, reads=reads)


def group(
    name: str,
    child_run: ChildRun,
    *children: Unit,
    for_each_item_in: Ref | None = None,
    run_if: Ref | None = None,
    reads: tuple[str, ...] = (),
) -> GroupUnit:
    """GroupUnit 을 짧게 만든다. 검사는 생성자가 한다."""
    return GroupUnit(name=name, child_run=child_run, children=children, for_each_item_in=for_each_item_in,
                     run_if=run_if, reads=reads)  # fmt: skip
