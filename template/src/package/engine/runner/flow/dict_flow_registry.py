"""DictFlowRegistry: 흐름 이름 → 흐름 정의를 dict 로 둔다."""

from __future__ import annotations

from collections.abc import Mapping

from package.engine.definition.flow_definition import FlowDefinition
from package.engine.runner.flow.flow_registry import FlowRegistry


class DictFlowRegistry(FlowRegistry):
    def __init__(self, flows: Mapping[str, FlowDefinition]) -> None:
        self._flows = dict(flows)

    def get(self, flow_name: str) -> FlowDefinition:
        if flow_name not in self._flows:
            raise KeyError(f"모르는 흐름입니다: {flow_name}")
        return self._flows[flow_name]

    def list(self) -> list[FlowDefinition]:
        return list(self._flows.values())
