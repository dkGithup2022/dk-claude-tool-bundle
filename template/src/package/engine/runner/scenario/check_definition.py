"""create 때: 흐름 정의를 실행 전에 검사한다."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from package.engine.definition.unit.group_unit import GroupUnit
from package.engine.definition.unit.task_unit import TaskUnit
from package.engine.definition.unit.unit import Unit
from package.engine.performer.accepts import ACCEPTS
from package.engine.performer.performed_by import PerformedBy
from package.engine.registry.registries import CONDITIONS, ITEM_SOURCES, TASKS


def check_definition(root: Unit, performers: Iterable[PerformedBy]) -> list[str]:
    """실행을 시작하기 전에 잡을 문제들. 빈 목록이면 시작해도 된다."""
    have = set(performers)
    problems: list[str] = []
    units: list[Unit] = []  # 실행 순서(위에서 아래, 앞에서 뒤)

    def walk(unit: Unit) -> None:
        units.append(unit)
        if unit.run_if and not CONDITIONS.has(unit.run_if.key):
            problems.append(f"{unit.name}: 등록되지 않은 조건 {unit.run_if.key}")
        if isinstance(unit, TaskUnit):
            if unit.performed_by not in have:
                problems.append(f"{unit.name}: 수행자가 없는 {unit.performed_by}")
            if not TASKS.has(unit.task.key):
                problems.append(f"{unit.name}: 등록되지 않은 작업 {unit.task.key}")
            else:
                made = getattr(TASKS.factory_of(unit.task.key), "request_type", None)
                need = ACCEPTS[unit.performed_by]
                if made is not need:
                    got = made.__name__ if made else "request_type 없음"
                    problems.append(f"{unit.name}: {unit.performed_by} 는 {need.__name__} 를 받는데 "
                                    f"{unit.task.key} 는 {got}")  # fmt: skip
                if getattr(TASKS.factory_of(unit.task.key), "output_kind", None) is None:
                    problems.append(f"{unit.name}: {unit.task.key} 에 output_kind 가 없다")
        elif isinstance(unit, GroupUnit):
            if unit.for_each_item_in and not ITEM_SOURCES.has(unit.for_each_item_in.key):
                problems.append(f"{unit.name}: 등록되지 않은 반복 항목 {unit.for_each_item_in.key}")
            for c in unit.children:
                walk(c)

    walk(root)
    problems += _check_names_and_reads(units)
    return problems


def _check_names_and_reads(units: list[Unit]) -> list[str]:
    """앞 결과는 노드 이름으로 읽으므로 이름이 겹치면 안 된다. 읽는 노드는 먼저 실행되는 작업이어야 한다."""
    problems = [f"노드 이름이 겹친다: {n}" for n, c in Counter(u.name for u in units).items() if c > 1]
    keys = Counter(u.task.key for u in units if isinstance(u, TaskUnit))
    problems += [f"같은 작업을 두 번 쓴다: {k}" for k, c in keys.items() if c > 1]
    order = {u.name: i for i, u in enumerate(units)}
    by_name = {u.name: u for u in units}
    for i, u in enumerate(units):
        for name in u.reads:
            if name not in by_name:
                problems.append(f"{u.name}: reads 의 노드가 없다: {name}")
            elif not isinstance(by_name[name], TaskUnit):
                problems.append(f"{u.name}: reads 의 노드가 작업이 아니다: {name}")
            elif order[name] >= i:
                problems.append(f"{u.name}: reads 의 노드가 먼저 실행되지 않는다: {name}")
    return problems
