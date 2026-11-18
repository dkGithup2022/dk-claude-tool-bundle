"""write_note: 말장난의 해설 메모를 서브에이전트가 산출물 폴더에 파일로 쓴다 (SUBAGENT, 결과 종류 FILES)."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.registry.registries import TASKS
from package.engine.request.subagent_request import SubagentRequest
from package.workflow.count_joke.write_note.build_write_note_message import build_write_note_message

AGENT = "package:joke-note-writer"  # plugin/agents/joke-note-writer.md


@TASKS.register_as("count_joke.write_note")
class WriteNoteTask(Task):
    request_type = SubagentRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> SubagentRequest:
        count = context.read("count_up")["count"]
        joke = context.read("make_joke")["joke"]
        return SubagentRequest(AGENT, build_write_note_message(count, joke, context.output_dir()))

    def build_output(self, context: FlowContext, result: None) -> TaskOutput:
        return TaskOutput()  # 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 모은다
