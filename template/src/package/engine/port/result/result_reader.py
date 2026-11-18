"""ResultReader: 노드 결과 읽기. 작업은 FlowContext 로 읽는다."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.definition.task.task_output import TaskOutput
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode


class ResultReader(ABC):
    @abstractmethod
    def read_result(self, state: FlowRunState, node: ScenarioNode, item_key: str) -> TaskOutput | None:
        """그 항목의 결과. 없으면 None."""

    @abstractmethod
    def read_files(self, state: FlowRunState, node: ScenarioNode, item_key: str, names: list[str]) -> dict[str, str]:
        """그 항목의 산출물 폴더에서 파일들을 텍스트로 읽는다. 파일 이름 → 내용."""
