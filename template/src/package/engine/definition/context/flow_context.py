"""작업이 실행 중에 쓸 수 있는 것만. 앞 노드 결과 읽기, 산출물 폴더, 지금 항목."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from package.engine.definition.context.node_locator import NodeLocator
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.output_missing_error import OutputMissingError
from package.engine.model.result.item_key import NO_ITEM_KEY
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.port.result.result_reader import ResultReader
from package.engine.port.result.result_writer import ResultWriter
from package.engine.runner.child_run.child_run import ChildRun


@dataclass(frozen=True, slots=True)
class FlowContext:
    """작업이 실행 중에 쓸 수 있는 것만. 앞 노드 결과 읽기, 산출물 폴더, 지금 항목."""

    state: FlowRunState
    node: ScenarioNode
    item_key: str | None
    result_reader: ResultReader
    result_writer: ResultWriter

    def read(self, node_name: str, item_key: str | None = None) -> dict[str, Any]:
        """앞 노드의 결과. 그 노드의 결과 종류가 DATA 면 result.json 의 dict, FILES 면 {파일 이름: 내용}.

        읽는 노드는 이 단위의 reads 에 적혀 있어야 한다.
        항목 키를 안 주면, 읽으려는 노드가 반복 몇 겹 안에 있는지만큼 지금 항목 키의 앞부분을 쓴다.
        """
        if node_name not in self.node.reads:
            raise ValueError(f"{self.node.name}: reads 에 없는 노드를 읽음: {node_name}")
        chain = NodeLocator(self.state.scenario).chain(node_name)
        target = chain[-1]
        key = item_key if item_key is not None else _default_key(chain, self.item_key)
        out = self.result_reader.read_result(self.state, target, key)
        if out is None:
            raise OutputMissingError(f"결과 없음: {node_name} [{key}]")
        if _output_kind(target) is OutputKind.FILES:
            return self.result_reader.read_files(self.state, target, key, out.data["files"])
        return out.data

    def output_dir(self) -> Path:
        """이 단계의 산출물 폴더. 서브에이전트에게 이 폴더에 쓰라고 알릴 때 쓴다. 폴더는 만들어 둔다."""
        return self.result_writer.output_dir(self.state, self.node, self.item_key or NO_ITEM_KEY)

    def current_item(self) -> Any:
        """지금 항목의 내용. 반복 밖이면 None. 항목 번호로 지난 데이터에서 찾는다 (find_item)."""
        # 레지스트리와의 순환 import 를 피하려고 여기서 import 한다
        from package.engine.definition.context.find_item import find_item

        return find_item(self)


def _output_kind(node: ScenarioNode) -> OutputKind:
    # Task·레지스트리와의 순환 import 를 피하려고 여기서 import 한다
    from package.engine.definition.task.task import Task
    from package.engine.registry.registries import TASKS

    assert node.task is not None
    return cast(type[Task], TASKS.factory_of(node.task.key)).output_kind


def _default_key(chain: list[ScenarioNode], current: str | None) -> str:
    """읽으려는 노드 위에 있는 반복의 수만큼 지금 항목 키의 앞부분. 반복이 없으면 NO_ITEM_KEY."""
    depth = sum(1 for n in chain[:-1] if n.child_run is ChildRun.FOR_EACH_ITEM)
    if depth == 0 or not current or current == NO_ITEM_KEY:
        return NO_ITEM_KEY
    return ".".join(current.split(".")[:depth])
