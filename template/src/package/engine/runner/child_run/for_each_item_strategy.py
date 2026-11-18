"""가장 바깥 반복은 처음 한 번 항목을 고정하고, 안쪽 반복은 매번 다시 계산한다. 키는 "2", "2.1"."""

from __future__ import annotations

from collections.abc import Iterator

from package.engine.definition.context.flow_context import FlowContext
from package.engine.model.result.item_key import NO_ITEM_KEY
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.registry.registries import ITEM_SOURCES
from package.engine.runner.child_run.child_run import ChildRun
from package.engine.runner.child_run.child_run_strategy import ChildRunStrategy


class ForEachItemStrategy(ChildRunStrategy):
    """가장 바깥 반복은 처음 한 번 항목을 고정하고, 안쪽 반복은 매번 다시 계산한다. 키는 "2", "2.1"."""

    child_run = ChildRun.FOR_EACH_ITEM

    def children_in_turn(self, node: ScenarioNode, context: FlowContext) -> Iterator[tuple[ScenarioNode, str]]:
        assert node.for_each_item_in is not None
        outer = context.item_key in (None, NO_ITEM_KEY)
        items = ITEM_SOURCES.create(node.for_each_item_in)(context)
        if outer:
            items = list(context.result_writer.fix_items(context.state, node, items).items)
            node.item_count = len(items)
        for i in range(1, len(items) + 1):
            key = str(i) if outer else f"{context.item_key}.{i}"
            for child in node.children:
                yield child, key  # 항목 내용은 작업이 FlowContext.current_item() 으로 찾는다
