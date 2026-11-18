"""흐름 실행의 진입점. 단위가 무슨 일을 하는지는 모른다."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.instruction.instruction import Instruction
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.session.claude_session import ClaudeSession


class FlowRunner(ABC):
    """흐름 실행의 진입점. 단위가 무슨 일을 하는지는 모른다."""

    @abstractmethod
    def start(self, session: ClaudeSession, flow_name: str) -> Instruction: ...

    @abstractmethod
    def next_instruction(self, session: ClaudeSession) -> Instruction: ...

    @abstractmethod
    def submit_reply(self, session: ClaudeSession, reply: str | None) -> Instruction: ...

    @abstractmethod
    def read_state(self, session: ClaudeSession) -> FlowRunState | None: ...

    @abstractmethod
    def cancel(self, session: ClaudeSession) -> Instruction: ...
