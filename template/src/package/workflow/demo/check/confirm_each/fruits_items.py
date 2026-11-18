"""check/confirm_each 의 반복 항목: collect_fruits 가 남긴 과일 목록."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.items_source import ItemsSource
from package.engine.registry.registries import ITEM_SOURCES


@ITEM_SOURCES.register_as("demo.fruits")
def fruits() -> ItemsSource:
    def items(context: FlowContext) -> list[str]:
        return list(context.read("collect_fruits")["items"])

    return items
