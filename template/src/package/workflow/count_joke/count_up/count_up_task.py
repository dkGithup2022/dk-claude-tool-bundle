"""count_up: 카운터를 1 올려 저장한다 (CODE). 로직은 model 의 Counter.up(), 저장은 port."""

from __future__ import annotations

from typing import Any

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.code_request import CodeRequest
from package.port.local.counter.default_counter_reader import DefaultCounterReader
from package.port.local.counter.default_counter_writer import DefaultCounterWriter


@TASKS.register_as("count_joke.count_up")
class CountUpTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        counter = DefaultCounterReader().read().up()
        DefaultCounterWriter().save(counter)
        return TaskOutput({"count": counter.value})
