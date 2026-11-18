"""bye: 워크플로가 끝났다고 보인다."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.show_request import ShowRequest


@TASKS.register_as("demo.bye")
class ByeTask(Task):
    request_type = ShowRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ShowRequest:
        return ShowRequest("가짜 흐름이 끝났습니다.")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({})
