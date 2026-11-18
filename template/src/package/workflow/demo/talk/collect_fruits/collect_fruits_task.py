"""talk/collect_fruits: 과일 목록을 결과로 남긴다 (코드로 수행). 실제 워크플로라면 앞 대화를 읽어 목록을 만든다."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.code_request import CodeRequest


@TASKS.register_as("demo.collect_fruits")
class CollectFruitsTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({"items": ["사과", "배"]})
