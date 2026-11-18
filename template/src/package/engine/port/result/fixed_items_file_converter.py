"""FixedItemsFileConverter: FixedItems ↔ <반복 노드 폴더>/items.json."""

from __future__ import annotations

from typing import Any

from package.engine.model.result.fixed_items import FixedItems


class FixedItemsFileConverter:
    def to_file(self, f: FixedItems) -> dict[str, Any]:
        return {"items": list(f.items), "fixed_at": f.fixed_at}

    def to_data(self, d: dict[str, Any]) -> FixedItems:
        return FixedItems(tuple(d["items"]), d["fixed_at"])
