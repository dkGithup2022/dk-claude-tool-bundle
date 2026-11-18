"""check/confirm_each/confirm: 반복 항목(과일) 하나마다 맞는지 묻는다."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.registry.registries import TASKS
from package.engine.request.question_request import QuestionRequest
from package.workflow.demo.check.choose_task import ChooseTask


@TASKS.register_as("demo.confirm")
class ConfirmTask(ChooseTask):
    choices = ("맞음", "아님")

    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest(f"{context.current_item()} 맞나요?", self.choices)
