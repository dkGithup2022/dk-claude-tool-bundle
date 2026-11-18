"""RunStateFileConverter: FlowRunState(시나리오 노드 트리, 기다리는 지시 포함) ↔ state.json."""

from __future__ import annotations

from typing import Any

from package.engine.definition.ref import Ref
from package.engine.instruction.instruction_converter import InstructionConverter
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.flow_run_status import FlowRunStatus
from package.engine.model.run_state.node_kind import NodeKind
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.performed_by import PerformedBy
from package.engine.runner.child_run.child_run import ChildRun


class RunStateFileConverter:
    def __init__(self) -> None:
        self.instructions = InstructionConverter()

    def to_file(self, st: FlowRunState) -> dict[str, Any]:
        waiting = st.waiting_instruction
        return {
            "run_id": st.run_id, "flow_name": st.flow_name, "session_id": st.session_id, "status": st.status.value,
            "created_at": st.created_at, "updated_at": st.updated_at, "scenario": self._node_to_file(st.scenario),
            "waiting_instruction": self.instructions.to_json(waiting) if waiting else None,
        }  # fmt: skip

    def to_data(self, d: dict[str, Any]) -> FlowRunState:
        waiting = d.get("waiting_instruction")
        return FlowRunState(
            d["run_id"], d["flow_name"], d["session_id"], FlowRunStatus(d["status"]), d["created_at"],
            d["updated_at"], self._node_to_data(d["scenario"]),
            self.instructions.to_data(waiting) if waiting else None,
        )  # fmt: skip

    def _node_to_file(self, n: ScenarioNode) -> dict[str, Any]:
        return {
            "uuid": n.uuid, "name": n.name, "kind": n.kind.value, "status": n.status.value,
            "performed_by": n.performed_by.value if n.performed_by else None,
            "child_run": n.child_run.value if n.child_run else None,
            "task": self._ref_to_file(n.task), "run_if": self._ref_to_file(n.run_if), "reads": list(n.reads),
            "for_each_item_in": self._ref_to_file(n.for_each_item_in),
            "item_count": n.item_count, "done_items": list(n.done_items), "waiting_item": n.waiting_item,
            "children": [self._node_to_file(c) for c in n.children],
        }  # fmt: skip

    def _node_to_data(self, d: dict[str, Any]) -> ScenarioNode:
        performed_by, child_run = d.get("performed_by"), d.get("child_run")
        return ScenarioNode(
            uuid=d["uuid"], name=d["name"], kind=NodeKind(d["kind"]), status=NodeStatus(d["status"]),
            performed_by=PerformedBy(performed_by) if performed_by else None,
            child_run=ChildRun(child_run) if child_run else None,
            task=self._ref_to_data(d.get("task")), run_if=self._ref_to_data(d.get("run_if")),
            reads=tuple(d.get("reads", [])),
            for_each_item_in=self._ref_to_data(d.get("for_each_item_in")),
            item_count=d.get("item_count"), done_items=list(d.get("done_items", [])),
            waiting_item=d.get("waiting_item"), children=[self._node_to_data(c) for c in d.get("children", [])],
        )  # fmt: skip

    def _ref_to_file(self, ref: Ref | None) -> dict[str, Any] | None:
        return None if ref is None else {"key": ref.key, "args": dict(ref.args)}

    def _ref_to_data(self, d: dict[str, Any] | None) -> Ref | None:
        return None if d is None else Ref(d["key"], dict(d.get("args", {})))
