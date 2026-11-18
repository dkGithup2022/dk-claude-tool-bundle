"""DefaultRunStateReader: state.json 을 읽는다."""

from __future__ import annotations

from package.common import files
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.port.run_location import run_dir
from package.engine.port.run_state.run_state_file_converter import RunStateFileConverter
from package.engine.port.run_state.run_state_reader import RunStateReader


class DefaultRunStateReader(RunStateReader):
    def load_run(self, session_id: str, run_id: str) -> FlowRunState:
        return RunStateFileConverter().to_data(files.read_json(run_dir(session_id, run_id) / "state.json"))
