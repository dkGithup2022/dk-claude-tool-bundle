"""SUBAGENT 가 받음 → 결과: 없음. 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 모은다."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubagentRequest:
    """SUBAGENT 가 받음 → 결과: 없음. 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 모은다."""

    agent: str
    message: str  # 산출물 폴더(FlowContext.output_dir())를 알려 준다
