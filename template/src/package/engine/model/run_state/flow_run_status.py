"""흐름 실행 하나의 상태."""

from __future__ import annotations

from enum import StrEnum


class FlowRunStatus(StrEnum):
    """흐름 실행 하나의 상태."""

    RUNNING = "running"
    FAILED = "failed"
    FINISHED = "finished"
    CANCELLED = "cancelled"
