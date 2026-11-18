"""RunStateReader: runs/<실행>/state.json 읽기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.run_state.flow_run_state import FlowRunState


class RunStateReader(ABC):
    @abstractmethod
    def load_run(self, session_id: str, run_id: str) -> FlowRunState:
        """없으면 FileNotFoundError."""
