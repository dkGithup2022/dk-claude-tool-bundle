"""Stop 훅: 멈추려 할 때 할 일이 남았으면 막는다."""

from __future__ import annotations

from typing import Any

from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.flow_run_status import FlowRunStatus
from package.engine.port.run_state.run_state_reader import RunStateReader
from package.engine.port.session.session_reader import SessionReader


def on_stop(sid: str, data: dict[str, Any], sessions: SessionReader, runs: RunStateReader) -> dict[str, Any] | None:
    """막는 때: 이 세션이 연 실행이 진행 중이고, 기다리는 지시가 없거나(next 차례) spawn 일 때."""
    if data.get("stop_hook_active"):
        return None
    session = sessions.load_session(sid)
    if session is None or session.active_run_id is None:
        return None
    state = runs.load_run(sid, session.active_run_id)
    if state.status is not FlowRunStatus.RUNNING:
        return None
    waiting = state.waiting_instruction
    if waiting is None:
        reason = "package 실행이 진행 중입니다. " + "package next 로 다음 지시를 받으세요."
        return {"decision": "block", "reason": reason}
    if waiting.type is InstructionType.SPAWN:
        reason = "서브에이전트를 띄우고, 완료 알림이 온 뒤 package done 을 부르세요."
        return {"decision": "block", "reason": reason}
    return None
