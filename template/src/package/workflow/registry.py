"""워크플로 이름 → FlowDefinition. start <이름> 이 여기서 찾는다. 새 워크플로를 만들면 여기 추가한다."""

from __future__ import annotations

from package.engine.definition.flow_definition import FlowDefinition
from package.workflow.count_joke.count_joke_flow import COUNT_JOKE_FLOW
from package.workflow.demo.demo_flow import DEMO_FLOW

FLOWS: dict[str, FlowDefinition] = {"demo": DEMO_FLOW, "count_joke": COUNT_JOKE_FLOW}
