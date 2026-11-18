"""실행 시나리오 안 노드 하나의 지금 상태."""

from __future__ import annotations

from enum import StrEnum


class NodeStatus(StrEnum):
    """실행 시나리오 안 노드 하나의 지금 상태."""

    PENDING = "pending"  # 아직 차례가 아님
    RUNNING = "running"  # 묶음 노드: 자식이 진행 중 / 반복: 일부 항목만 끝남
    WAITING = "waiting"  # 메인 세션의 답을 기다림
    COMPLETED = "completed"
    SKIPPED = "skipped"  # run_if 가 거짓
    FAILED = "failed"
