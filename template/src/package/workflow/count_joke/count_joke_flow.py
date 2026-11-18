"""count_joke 워크플로 선언.

카운터를 올리고(코드), 그 숫자로 말장난을 만들고(LLM), 해설 메모를 쓰게 하고(서브에이전트), 보인다.
"""

from __future__ import annotations

from package.engine.definition.flow_definition import FlowDefinition
from package.engine.definition.ref import Ref
from package.engine.definition.unit.builders import group, task
from package.engine.performer.performed_by import PerformedBy
from package.engine.runner.child_run.child_run import ChildRun
from package.workflow.count_joke.count_up import count_up_task  # noqa: F401
from package.workflow.count_joke.make_joke import make_joke_task  # noqa: F401
from package.workflow.count_joke.show_joke import show_joke_task  # noqa: F401
from package.workflow.count_joke.write_note import write_note_task  # noqa: F401

COUNT_JOKE_FLOW = FlowDefinition(
    name="count_joke",
    description="카운터를 올리고 그 숫자로 말장난을 하고 해설 메모를 남긴다",
    root=group("count_joke", ChildRun.IN_ORDER,
        task("count_up", PerformedBy.CODE, Ref("count_joke.count_up")),
        task("make_joke", PerformedBy.CLAUDE_P, Ref("count_joke.make_joke"), reads=("count_up",)),
        task("write_note", PerformedBy.SUBAGENT, Ref("count_joke.write_note"), reads=("count_up", "make_joke")),
        task("show_joke", PerformedBy.MAIN_SESSION_SHOW, Ref("count_joke.show_joke"),
             reads=("make_joke", "write_note"))),
)  # fmt: skip
