"""DefaultResultReader: 노드 폴더의 result.json 을 읽는다."""

from __future__ import annotations

from package.common import files
from package.engine.definition.task.task_output import TaskOutput
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.port.result.node_result_file_converter import NodeResultFileConverter
from package.engine.port.result.result_reader import ResultReader
from package.engine.port.run_location import node_dir, output_dir


class DefaultResultReader(ResultReader):
    def read_result(self, state: FlowRunState, node: ScenarioNode, item_key: str) -> TaskOutput | None:
        p = node_dir(state, node) / "result.json"
        if not p.exists():
            return None
        data = NodeResultFileConverter().to_data(files.read_json(p)).by_item.get(item_key)
        return None if data is None else TaskOutput(data)

    def read_files(self, state: FlowRunState, node: ScenarioNode, item_key: str, names: list[str]) -> dict[str, str]:
        d = output_dir(state, node, item_key)
        return {name: (d / name).read_text(encoding="utf-8") for name in names}
