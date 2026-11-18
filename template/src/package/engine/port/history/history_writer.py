"""HistoryWriter: runs/<실행>/history.jsonl 에 한 줄 덧붙이기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.history.history_entry import HistoryEntry
from package.engine.model.run_state.flow_run_state import FlowRunState


class HistoryWriter(ABC):
    @abstractmethod
    def append_history(self, state: FlowRunState, entry: HistoryEntry) -> None: ...
