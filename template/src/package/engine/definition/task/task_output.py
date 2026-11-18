"""작업 하나(항목 하나)의 결과. 결과 종류(OutputKind)에 맞는 필드 하나만 채운다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskOutput:
    """작업 하나(항목 하나)의 결과. 결과 종류(OutputKind)에 맞는 필드 하나만 채운다."""

    data: dict[str, Any] = field(default_factory=dict)  # DATA: <노드 폴더>/result.json 의 항목 번호 키 값으로 저장
    files: dict[str, str] = field(default_factory=dict)  # FILES: 파일 이름 → 내용. engine 이 산출물 폴더에 쓴다
