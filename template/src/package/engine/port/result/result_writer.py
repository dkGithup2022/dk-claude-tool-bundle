"""ResultWriter: 노드 결과, 반복 항목, claude -p 호출 기록 쓰기."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord
from package.engine.definition.task.task_output import TaskOutput
from package.engine.model.result.fixed_items import FixedItems
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode


class ResultWriter(ABC):
    @abstractmethod
    def save_result(self, state: FlowRunState, node: ScenarioNode, item_key: str, output: TaskOutput) -> str:
        """결과를 그 항목 번호로 저장하고 history 에 적을 위치(result_ref)를 돌려준다."""

    @abstractmethod
    def output_dir(self, state: FlowRunState, node: ScenarioNode, item_key: str) -> Path:
        """그 항목의 산출물 폴더. 만들어 두고 돌려준다."""

    @abstractmethod
    def save_files(self, state: FlowRunState, node: ScenarioNode, item_key: str, contents: dict[str, str]) -> list[str]:
        """파일 이름 → 내용을 산출물 폴더에 쓰고, 폴더에 있는 파일 전부의 이름(폴더 기준 경로)을 돌려준다."""

    @abstractmethod
    def fix_items(self, state: FlowRunState, node: ScenarioNode, items: list[Any]) -> FixedItems:
        """반복 항목을 처음 한 번 고정한다. 이미 있으면 있는 것을 돌려준다."""

    @abstractmethod
    def save_prompt_call(self, state: FlowRunState, node: ScenarioNode, record: PromptCallRecord) -> str:
        """claude -p 호출 기록을 calls/<n>/ 에 저장하고 그 경로를 돌려준다."""
