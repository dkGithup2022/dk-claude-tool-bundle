"""check 아래의 묻기 작업들이 같이 쓰는 부모. 선택지 밖의 답은 받지 않는다."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.reply_rejected_error import ReplyRejectedError
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.request.question_request import QuestionRequest


class ChooseTask(Task):
    request_type = QuestionRequest
    output_kind = OutputKind.DATA
    choices: tuple[str, ...] = ()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        if result not in self.choices:
            raise ReplyRejectedError(f"선택지 밖의 답: {result}")
        return TaskOutput({"answer": result})
