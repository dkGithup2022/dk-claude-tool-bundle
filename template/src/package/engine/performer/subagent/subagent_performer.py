"""SubagentPerformer: 메인 세션이 서브에이전트를 띄운다. 서브에이전트가 끝나 done 을 받으면 끝난다."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.main_session.main_session_performer import _MainSessionPerformer
from package.engine.performer.performed_by import PerformedBy


class SubagentPerformer(_MainSessionPerformer):
    """결과: 없음. 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 결과로 모은다 (Task 의 결과 종류가 FILES 일 때)."""

    performed_by = PerformedBy.SUBAGENT
    instruction_type = InstructionType.SPAWN

    def receive_reply(self, node: ScenarioNode, reply: str | None, context: FlowContext) -> None:
        return None
