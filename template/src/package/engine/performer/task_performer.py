"""수행자 하나의 실행기. PerformedBy 값마다 하나."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from package.engine.definition.context.flow_context import FlowContext
from package.engine.instruction.instruction import Instruction
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.accepts import ACCEPTS
from package.engine.performer.performed_by import PerformedBy
from package.engine.request.task_request import TaskRequest


class TaskPerformer(ABC):
    """수행자 하나의 실행기. PerformedBy 값마다 하나."""

    performed_by: ClassVar[PerformedBy]

    @property
    def accepts(self) -> type[TaskRequest]:  # ACCEPTS 한 곳에서
        return ACCEPTS[self.performed_by]

    @abstractmethod
    def perform(self, node: ScenarioNode, request: TaskRequest, context: FlowContext) -> Instruction | Any:
        """바로 끝나면 결과를, 메인 세션에 맡겨야 하면 Instruction 을 돌려준다."""

    def receive_reply(self, node: ScenarioNode, reply: str | None, context: FlowContext) -> Any:
        """메인 세션이 돌려준 처리 결과를 작업에 넘길 결과로 바꾼다."""
        raise RuntimeError(f"{self.performed_by} 는 답을 받지 않는다")
