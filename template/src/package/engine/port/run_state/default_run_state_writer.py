"""DefaultRunStateWriter: state.json 을 쓴다."""

from __future__ import annotations

from package.common import files
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.port.run_location import run_dir
from package.engine.port.run_state.run_state_file_converter import RunStateFileConverter
from package.engine.port.run_state.run_state_writer import RunStateWriter


class DefaultRunStateWriter(RunStateWriter):
    def save_run(self, state: FlowRunState) -> None:
        files.write_json(run_dir(state.session_id, state.run_id) / "state.json", RunStateFileConverter().to_file(state))
