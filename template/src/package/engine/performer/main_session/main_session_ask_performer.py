"""MainSessionAskPerformer: 메인 세션이 선택지로 묻는다. 빈 답은 다시 묻는다."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.reply_rejected_error import ReplyRejectedError
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.main_session.main_session_performer import _MainSessionPerformer
from package.engine.performer.performed_by import PerformedBy


class MainSessionAskPerformer(_MainSessionPerformer):
    performed_by = PerformedBy.MAIN_SESSION_ASK
    instruction_type = InstructionType.ASK

    def receive_reply(self, node: ScenarioNode, reply: str | None, context: FlowContext) -> str:
        answer = (reply or "").strip()
        if not answer:
            raise ReplyRejectedError("빈 답")  # 빈 답은 공통으로 다시 묻기
        return answer
