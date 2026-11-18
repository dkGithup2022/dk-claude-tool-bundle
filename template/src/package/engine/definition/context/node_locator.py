"""NodeLocator: 노드 이름으로 시나리오에서 노드를 찾는다. 워크플로 안에서 노드 이름은 겹치지 않는다 (시작 전 검사)."""

from __future__ import annotations

from package.engine.model.run_state.scenario_node import ScenarioNode


class NodeLocator:
    """노드 이름으로 시나리오에서 노드를 찾는다. 워크플로 안에서 노드 이름은 겹치지 않는다 (시작 전 검사)."""

    def __init__(self, root: ScenarioNode) -> None:
        self.root = root

    def chain(self, name: str) -> list[ScenarioNode]:
        """맨 위 노드 아래에서 그 노드까지 (맨 위 제외, 그 노드 포함). 반복 몇 겹 안인지 셀 때 쓴다. 없으면 KeyError."""
        found = self._search(self.root, name)
        if found is None:
            raise KeyError(f"시나리오에 없는 노드: {name}")
        return found[1:]

    def _search(self, node: ScenarioNode, name: str) -> list[ScenarioNode] | None:
        if node.name == name:
            return [node]
        for child in node.children:
            found = self._search(child, name)
            if found is not None:
                return [node, *found]
        return None
