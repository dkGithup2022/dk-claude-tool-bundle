"""실행 시나리오의 노드 하나. create 때 흐름 정의를 따라 만들고 uuid 를 붙인다."""

from __future__ import annotations

from dataclasses import dataclass, field

from package.engine.definition.ref import Ref
from package.engine.model.run_state.node_kind import NodeKind
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.performer.performed_by import PerformedBy
from package.engine.runner.child_run.child_run import ChildRun


@dataclass(slots=True)
class ScenarioNode:
    """실행 시나리오의 노드 하나. create 때 흐름 정의를 따라 만들고 uuid 를 붙인다."""

    uuid: str
    name: str
    kind: NodeKind
    status: NodeStatus = NodeStatus.PENDING
    performed_by: PerformedBy | None = None  # TASK 일 때
    child_run: ChildRun | None = None  # GROUP 일 때
    task: Ref | None = None  # TASK 일 때: TASKS 의 키와 인자
    run_if: Ref | None = None  # CONDITIONS 의 키와 인자
    reads: tuple[str, ...] = ()  # 결과를 읽는 앞 노드의 이름 (정의 그대로)
    for_each_item_in: Ref | None = None  # FOR_EACH_ITEM 일 때: ITEM_SOURCES 의 키와 인자
    item_count: int | None = None  # FOR_EACH_ITEM: 항목을 고정할 때 적음
    done_items: list[str] = field(default_factory=list)  # 반복 안: 끝난 항목 번호
    waiting_item: str | None = None  # 반복 안: 답을 기다리는 항목 번호
    children: list[ScenarioNode] = field(default_factory=list)

    @property
    def folder_name(self) -> str:
        return f"{self.name}_{self.uuid[:8]}"
