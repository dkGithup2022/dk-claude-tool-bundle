"""CodePerformer: 코드가 바로 수행한다 (일은 작업의 build_output 이 함)."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.performed_by import PerformedBy
from package.engine.performer.task_performer import TaskPerformer
from package.engine.request.task_request import TaskRequest


class CodePerformer(TaskPerformer):
    performed_by = PerformedBy.CODE

    def perform(self, node: ScenarioNode, request: TaskRequest, context: FlowContext) -> Any:
        return None  # 일은 build_output 이 한다
