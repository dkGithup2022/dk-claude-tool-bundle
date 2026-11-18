"""DefaultHistoryWriter: history.jsonl 에 한 줄 덧붙인다."""

from __future__ import annotations

from package.common import files
from package.engine.model.history.history_entry import HistoryEntry
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.port.history.history_file_converter import HistoryFileConverter
from package.engine.port.history.history_writer import HistoryWriter
from package.engine.port.run_location import run_dir


class DefaultHistoryWriter(HistoryWriter):
    def append_history(self, state: FlowRunState, entry: HistoryEntry) -> None:
        files.append_jsonl(
            run_dir(state.session_id, state.run_id) / "history.jsonl", HistoryFileConverter().to_file(entry)
        )
