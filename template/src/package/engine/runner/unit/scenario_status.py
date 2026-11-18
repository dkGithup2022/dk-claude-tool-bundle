"""시나리오 노드 상태를 보고 바꾸는 함수들 (끝났나, 실패 되돌리기, 반복 끝 정리)."""

from __future__ import annotations

from package.common.clock import utc_now
from package.engine.model.result.item_key import NO_ITEM_KEY
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.model.run_state.scenario_node import ScenarioNode

now = utc_now


def _is_done(node: ScenarioNode, key: str) -> bool:
    if key == NO_ITEM_KEY:
        return node.status in (NodeStatus.COMPLETED, NodeStatus.SKIPPED)
    return key in node.done_items


def _find_uuid(node: ScenarioNode, uuid: str) -> ScenarioNode | None:
    if node.uuid == uuid:
        return node
    for c in node.children:
        if (found := _find_uuid(c, uuid)) is not None:
            return found
    return None


def _complete_descendants(node: ScenarioNode) -> None:
    """반복이 다 끝나면 그 아래에서 RUNNING 으로 남은 노드를 COMPLETED 로."""
    for c in node.children:
        if c.status is NodeStatus.RUNNING:
            c.status = NodeStatus.COMPLETED
        _complete_descendants(c)


def _reset_failed(node: ScenarioNode) -> None:
    if node.status is NodeStatus.FAILED:
        node.status = NodeStatus.RUNNING if node.done_items else NodeStatus.PENDING
    for c in node.children:
        _reset_failed(c)
