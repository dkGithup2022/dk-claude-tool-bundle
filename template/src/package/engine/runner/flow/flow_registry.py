"""FlowRegistry: 흐름 이름으로 흐름 정의를 찾는 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.definition.flow_definition import FlowDefinition


class FlowRegistry(ABC):
    @abstractmethod
    def get(self, flow_name: str) -> FlowDefinition: ...

    @abstractmethod
    def list(self) -> list[FlowDefinition]: ...
