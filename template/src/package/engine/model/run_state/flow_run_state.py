"""sessions/<session_id>/runs/<run_id>/state.json"""

from __future__ import annotations

from dataclasses import dataclass

from package.engine.instruction.instruction import Instruction
from package.engine.model.run_state.flow_run_status import FlowRunStatus
from package.engine.model.run_state.scenario_node import ScenarioNode


@dataclass(slots=True)
class FlowRunState:
    """sessions/<session_id>/runs/<run_id>/state.json"""

    run_id: str
    flow_name: str
    session_id: str
    status: FlowRunStatus
    created_at: str
    updated_at: str
    scenario: ScenarioNode  # 노드 트리, uuid, 각 노드의 상태
    waiting_instruction: Instruction | None  # 메인 세션이 처리 중인 지시
