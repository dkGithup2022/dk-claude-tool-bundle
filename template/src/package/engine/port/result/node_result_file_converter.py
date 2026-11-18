"""NodeResultFileConverter: NodeResult ↔ <노드 폴더>/result.json."""

from __future__ import annotations

from typing import Any

from package.engine.model.result.node_result import NodeResult


class NodeResultFileConverter:
    def to_file(self, r: NodeResult) -> dict[str, Any]:
        return {"by_item": {k: dict(v) for k, v in r.by_item.items()}}

    def to_data(self, d: dict[str, Any]) -> NodeResult:
        return NodeResult({k: dict(v) for k, v in d.get("by_item", {}).items()})
