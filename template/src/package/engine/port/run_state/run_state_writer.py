"""RunStateWriter: runs/<실행>/state.json 쓰기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.run_state.flow_run_state import FlowRunState


class RunStateWriter(ABC):
    @abstractmethod
    def save_run(self, state: FlowRunState) -> None: ...
