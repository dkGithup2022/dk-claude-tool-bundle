"""PromptSpec: claude -p 호출 하나의 설정 (프롬프트 파일, 출력 데이터 클래스, 모델, 시간 제한)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PromptSpec:
    name: str
    prompt_file: Path  # prompt_{동작이름}.md
    output_type: type[Any]  # prompt_{동작이름}_output.py 의 데이터 클래스. 출력 JSON 스키마는 여기서 만든다
    model: str = "sonnet"
    timeout_seconds: int = 300
