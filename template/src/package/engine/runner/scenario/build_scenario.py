"""create 때: 흐름 정의를 따라 실행 시나리오를 만든다."""

from __future__ import annotations

import uuid

from package.engine.definition.unit.group_unit import GroupUnit
from package.engine.definition.unit.task_unit import TaskUnit
from package.engine.definition.unit.unit import Unit
from package.engine.model.run_state.node_kind import NodeKind
from package.engine.model.run_state.scenario_node import ScenarioNode


def build_scenario(unit: Unit) -> ScenarioNode:
    """정의를 따라 시나리오를 만든다. 노드마다 uuid, 상태 PENDING."""
    if isinstance(unit, TaskUnit):
        return ScenarioNode(uuid=str(uuid.uuid4()), name=unit.name, kind=NodeKind.TASK,
                            performed_by=unit.performed_by, task=unit.task, run_if=unit.run_if,
                            reads=unit.reads)  # fmt: skip
    assert isinstance(unit, GroupUnit)
    return ScenarioNode(uuid=str(uuid.uuid4()), name=unit.name, kind=NodeKind.GROUP, child_run=unit.child_run,
                        run_if=unit.run_if, reads=unit.reads, for_each_item_in=unit.for_each_item_in,
                        children=[build_scenario(c) for c in unit.children])  # fmt: skip
