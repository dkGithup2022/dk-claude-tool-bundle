"""DefaultResultWriter: 노드 결과, 반복 항목, claude -p 호출 기록을 노드 폴더에 쓴다."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord
from package.common import files
from package.common.clock import utc_now
from package.engine.definition.task.task_output import TaskOutput
from package.engine.model.result.fixed_items import FixedItems
from package.engine.model.result.node_result import NodeResult
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.port.result.fixed_items_file_converter import FixedItemsFileConverter
from package.engine.port.result.node_result_file_converter import NodeResultFileConverter
from package.engine.port.result.prompt_call_file_converter import PromptCallFileConverter
from package.engine.port.result.result_writer import ResultWriter
from package.engine.port.run_location import node_dir, output_dir


class DefaultResultWriter(ResultWriter):
    def save_result(self, state: FlowRunState, node: ScenarioNode, item_key: str, output: TaskOutput) -> str:
        p = node_dir(state, node) / "result.json"
        result = NodeResultFileConverter().to_data(files.read_json(p)) if p.exists() else NodeResult({})
        result.by_item[item_key] = dict(output.data)
        files.write_json(p, NodeResultFileConverter().to_file(result))
        return f"{node.folder_name}/result.json#{item_key}"

    def output_dir(self, state: FlowRunState, node: ScenarioNode, item_key: str) -> Path:
        d = output_dir(state, node, item_key)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_files(self, state: FlowRunState, node: ScenarioNode, item_key: str, contents: dict[str, str]) -> list[str]:
        d = self.output_dir(state, node, item_key)
        for name, text in contents.items():
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"산출물 파일 이름은 산출물 폴더 안의 경로여야 한다: {name!r}")
            files.write_text(d / name, text)
        return sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())

    def fix_items(self, state: FlowRunState, node: ScenarioNode, items: list[Any]) -> FixedItems:
        p = node_dir(state, node) / "items.json"
        if p.exists():
            return FixedItemsFileConverter().to_data(files.read_json(p))
        fixed = FixedItems(tuple(items), utc_now())
        files.write_json(p, FixedItemsFileConverter().to_file(fixed))
        return fixed

    def save_prompt_call(self, state: FlowRunState, node: ScenarioNode, record: PromptCallRecord) -> str:
        base = node_dir(state, node) / "calls"
        used = [int(d.name) for d in base.iterdir() if d.name.isdigit()] if base.exists() else []
        d = base / str(max(used, default=0) + 1)
        request, response = PromptCallFileConverter().to_file(record)
        files.write_json(d / "request.json", request)
        files.write_json(d / "response.json", response)
        return f"{node.folder_name}/calls/{d.name}"
