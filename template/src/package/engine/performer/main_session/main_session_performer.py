"""메인 세션에 맡기는 수행자들의 공통 부분: 요청을 지시로 바꿔 돌려준다."""

from __future__ import annotations

from typing import ClassVar

from package.engine.definition.context.flow_context import FlowContext
from package.engine.instruction.instruction import Instruction
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.task_performer import TaskPerformer
from package.engine.request.task_request import TaskRequest


class _MainSessionPerformer(TaskPerformer):
    instruction_type: ClassVar[InstructionType]

    def perform(self, node: ScenarioNode, request: TaskRequest, context: FlowContext) -> Instruction:
        return Instruction(self.instruction_type, node.uuid, context.item_key, request)
