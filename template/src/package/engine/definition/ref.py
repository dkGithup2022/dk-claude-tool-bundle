"""레지스트리 항목을 가리키는 참조. state.json 에 그대로 저장된다 (args 는 JSON 으로 쓸 수 있는 값만)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Ref:
    """레지스트리 항목을 가리키는 참조. state.json 에 그대로 저장된다 (args 는 JSON 으로 쓸 수 있는 값만)."""

    key: str
    args: dict[str, Any] = field(default_factory=dict)
