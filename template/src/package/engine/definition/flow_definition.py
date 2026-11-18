"""FlowDefinition: 흐름 하나의 정의 (이름, 설명, 맨 위 단위)."""

from __future__ import annotations

from dataclasses import dataclass

from package.engine.definition.unit.unit import Unit


@dataclass(frozen=True, slots=True)
class FlowDefinition:
    name: str
    description: str  # 처음 보는 세션에 보일 설명 (백로그 1)
    root: Unit
