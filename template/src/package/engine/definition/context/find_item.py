"""find_item: 지금 항목 번호로 그 항목의 내용을 지난 데이터에서 다시 찾는다.

가장 바깥 반복은 고정해 둔 항목 파일(items.json)에서, 안쪽 반복은 바깥 항목에서 목록을 다시 계산해 찾는다.
예: 항목 "2" → 고정된 후보 목록의 2번째. 항목 "2.1" → 2번째 후보의 질문 목록을 다시 만들어 그 1번째.
"""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.model.result.item_key import NO_ITEM_KEY
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.registry.registries import ITEM_SOURCES
from package.engine.runner.child_run.child_run import ChildRun


def find_item(context: FlowContext) -> Any:
    """반복 밖이면 None."""
    if context.item_key in (None, NO_ITEM_KEY):
        return None
    keys = context.item_key.split(".")
    ancestors = path_to(context.state.scenario, context.node.uuid)[:-1]
    loops = [n for n in ancestors if n.child_run is ChildRun.FOR_EACH_ITEM]
    loop = loops[len(keys) - 1]  # 이 항목 번호를 만든 반복 (안쪽일수록 번호가 길다)
    parent_key = ".".join(keys[:-1]) or NO_ITEM_KEY
    loop_context = FlowContext(context.state, loop, parent_key, context.result_reader, context.result_writer)
    assert loop.for_each_item_in is not None
    items = ITEM_SOURCES.create(loop.for_each_item_in)(loop_context)
    if parent_key == NO_ITEM_KEY:  # 가장 바깥 반복: 고정해 둔 목록
        items = list(context.result_writer.fix_items(context.state, loop, items).items)
    return items[int(keys[-1]) - 1]


def path_to(root: ScenarioNode, uuid: str) -> list[ScenarioNode]:
    """맨 위 노드부터 그 노드까지 (그 노드 포함). 없으면 빈 목록."""
    if root.uuid == uuid:
        return [root]
    for child in root.children:
        found = path_to(child, uuid)
        if found:
            return [root, *found]
    return []
