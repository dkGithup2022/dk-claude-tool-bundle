"""HistoryFileConverter: HistoryEntry ↔ history.jsonl 한 줄."""

from __future__ import annotations

from typing import Any

from package.engine.model.history.history_entry import HistoryEntry
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.performer.performed_by import PerformedBy


class HistoryFileConverter:
    def to_file(self, e: HistoryEntry) -> dict[str, Any]:
        return {
            "at": e.at, "node_uuid": e.node_uuid, "node_folder": e.node_folder, "item_key": e.item_key,
            "status": e.status.value, "performed_by": e.performed_by.value if e.performed_by else None,
            "result_ref": e.result_ref, "call_files": list(e.call_files), "cost_usd": e.cost_usd,
            "seconds": e.seconds, "note": e.note,
        }  # fmt: skip

    def to_data(self, d: dict[str, Any]) -> HistoryEntry:
        performed_by = d.get("performed_by")
        return HistoryEntry(
            d["at"], d["node_uuid"], d["node_folder"], d.get("item_key"), NodeStatus(d["status"]),
            PerformedBy(performed_by) if performed_by else None, d.get("result_ref"), tuple(d.get("call_files", ())),
            d.get("cost_usd"), d.get("seconds"), d.get("note"),
        )  # fmt: skip
