"""PromptFile: claude -p 가 돌려주는 파일 하나.

결과가 파일인 프롬프트는 출력 데이터 클래스에 list[PromptFile] 필드를 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptFile:
    """claude -p 가 돌려주는 파일 하나."""

    name: str  # 파일 이름. 예: "aa.md"
    content: str  # 파일 내용 전체 (길어도 됨)
