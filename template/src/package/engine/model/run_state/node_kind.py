"""NodeKind: 시나리오 노드의 종류 (작업 하나 / 묶음)."""

from __future__ import annotations

from enum import StrEnum


class NodeKind(StrEnum):
    TASK = "task"
    GROUP = "group"
