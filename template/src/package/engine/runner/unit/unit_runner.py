"""모든 단위에 같은 순서를 강제한다."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.instruction.instruction import Instruction
from package.engine.model.run_state.flow_run_state import FlowRunState


class UnitRunner(ABC):
    """모든 단위에 같은 순서를 강제한다.

    끝났나 확인 → run_if 확인 → (작업 단위) 요청 만들기 → 수행 → 결과 저장 → 끝 표시 → 기록
                              (묶음 단위) 차례인 자식에게 같은 순서
    """

    @abstractmethod
    def next_instruction(self, state: FlowRunState) -> Instruction | None:
        """시나리오에서 다음 차례 노드를 찾아 수행한다. 메인 세션에 맡길 것이 없으면 None (끝)."""

    @abstractmethod
    def submit_reply(self, state: FlowRunState, reply: str | None) -> Instruction | None:
        """기다리던 노드에 답을 넘기고 결과를 기록한다. 다시 물을 때나 실패하면 그 지시를 돌려준다."""
