"""talk/listen: 좋아하는 과일을 사용자와 대화로 듣는다. 결과는 대화 구간과 대화 기록 경로."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.conversation_request import ConversationRequest


@TASKS.register_as("demo.listen")
class ListenTask(Task):
    request_type = ConversationRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ConversationRequest:
        return ConversationRequest(goal="좋아하는 과일 두세 개를 듣는다", opening="좋아하는 과일이 뭐예요?")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput(dict(result))
