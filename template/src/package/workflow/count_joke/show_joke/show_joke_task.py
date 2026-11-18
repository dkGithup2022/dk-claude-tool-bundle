"""show_joke: make_joke 의 말장난과 write_note 의 해설 메모를 사용자에게 보인다 (SHOW)."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.show_request import ShowRequest


@TASKS.register_as("count_joke.show_joke")
class ShowJokeTask(Task):
    request_type = ShowRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ShowRequest:
        joke = context.read("make_joke")["joke"]
        notes = context.read("write_note")  # FILES: 파일 이름 → 내용
        return ShowRequest("\n\n".join([joke, *notes.values()]))

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({})
