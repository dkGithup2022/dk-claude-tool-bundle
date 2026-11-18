"""runs/<run_id>/history.jsonl 한 줄. 덧붙이기만 한다."""

from __future__ import annotations

from dataclasses import dataclass

from package.engine.model.run_state.node_status import NodeStatus
from package.engine.performer.performed_by import PerformedBy


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """runs/<run_id>/history.jsonl 한 줄. 덧붙이기만 한다."""

    at: str
    node_uuid: str
    node_folder: str
    item_key: str | None  # 반복 안이면 항목 번호
    status: NodeStatus  # WAITING / COMPLETED / SKIPPED / FAILED
    performed_by: PerformedBy | None
    result_ref: str | None = None  # "alarm_a7c2f0e1/result.json#2"
    call_files: tuple[str, ...] = ()  # claude -p 호출 기록
    cost_usd: float | None = None
    seconds: float | None = None
    note: str | None = None  # 실패 내용 등
