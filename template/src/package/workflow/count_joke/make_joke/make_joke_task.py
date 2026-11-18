"""make_joke: count_up 의 숫자로 말장난을 만든다 (CLAUDE_P)."""

from __future__ import annotations

from pathlib import Path

from package.claude_utils.prompt.dto.prompt_spec import PromptSpec
from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.prompt_request import PromptRequest
from package.workflow.count_joke.make_joke.prompt_make_joke_output import MakeJokeOutput

MAKE_JOKE = PromptSpec(
    name="make_joke",
    prompt_file=Path(__file__).parent / "prompt_make_joke.md",
    output_type=MakeJokeOutput,
)


@TASKS.register_as("count_joke.make_joke")
class MakeJokeTask(Task):
    request_type = PromptRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> PromptRequest:
        count = context.read("count_up")["count"]
        return PromptRequest(MAKE_JOKE, f"숫자: {count}")

    def build_output(self, context: FlowContext, result: MakeJokeOutput) -> TaskOutput:
        return TaskOutput({"joke": result.joke.strip()})
