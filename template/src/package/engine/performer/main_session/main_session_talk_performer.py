"""MainSessionTalkPerformer: 메인 세션이 대화한다. 결과는 대화 구간과 대화 기록 경로."""

from __future__ import annotations

from typing import Any

from package.common.clock import utc_now
from package.engine.definition.context.flow_context import FlowContext
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.main_session.main_session_performer import _MainSessionPerformer
from package.engine.performer.performed_by import PerformedBy
from package.engine.port.session.session_reader import SessionReader


class MainSessionTalkPerformer(_MainSessionPerformer):
    """결과: 대화 구간 {from: 실행 시작, to: 답을 받은 시각, transcript: 대화 기록 경로}."""

    performed_by = PerformedBy.MAIN_SESSION_TALK
    instruction_type = InstructionType.TALK

    def __init__(self, session_reader: SessionReader) -> None:
        self.session_reader = session_reader

    def receive_reply(self, node: ScenarioNode, reply: str | None, context: FlowContext) -> dict[str, Any]:
        session = self.session_reader.load_session(context.state.session_id)
        return {"from": context.state.created_at, "to": utc_now(),
                "transcript": session.transcript_path if session else None}  # fmt: skip
