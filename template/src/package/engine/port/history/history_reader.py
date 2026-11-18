"""HistoryReader: runs/<실행>/history.jsonl 읽기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.history.history_entry import HistoryEntry
from package.engine.model.run_state.flow_run_state import FlowRunState


class HistoryReader(ABC):
    @abstractmethod
    def read_history(self, state: FlowRunState) -> list[HistoryEntry]:
        """history 를 다시 읽는다 (요약 등)."""
