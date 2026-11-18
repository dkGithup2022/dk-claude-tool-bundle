"""메인 세션에 내리는 지시의 종류."""

from __future__ import annotations

from enum import StrEnum


class InstructionType(StrEnum):
    """메인 세션에 내리는 지시의 종류."""

    SHOW = "show"
    ASK = "ask"
    TALK = "talk"
    SPAWN = "spawn"
    FINISHED = "finished"
    FAILED = "failed"
