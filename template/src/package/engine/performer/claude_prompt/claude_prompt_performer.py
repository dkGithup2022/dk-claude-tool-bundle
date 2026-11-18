"""ClaudePromptPerformer: claude -p 로 수행하고 호출 기록을 노드 폴더에 남긴다."""

from __future__ import annotations

from package.claude_utils.prompt.call_prompt import call_prompt
from package.claude_utils.prompt.prompt_call_error import PromptCallError
from package.engine.definition.context.flow_context import FlowContext
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.performer.call_outcome import CallOutcome
from package.engine.performer.claude_prompt.recorded_prompt_call_error import RecordedPromptCallError
from package.engine.performer.performed_by import PerformedBy
from package.engine.performer.task_performer import TaskPerformer
from package.engine.request.prompt_request import PromptRequest
from package.engine.request.task_request import TaskRequest


class ClaudePromptPerformer(TaskPerformer):
    performed_by = PerformedBy.CLAUDE_P

    def perform(self, node: ScenarioNode, request: TaskRequest, context: FlowContext) -> CallOutcome:
        assert isinstance(request, PromptRequest)
        try:
            result, record = call_prompt(request.spec, request.input_text)
        except PromptCallError as e:
            ref = context.result_writer.save_prompt_call(context.state, node, e.record)
            raise RecordedPromptCallError(str(e), ref, e.record.response.get("cost_usd"),
                                        e.record.response.get("seconds")) from e  # fmt: skip
        ref = context.result_writer.save_prompt_call(context.state, node, record)
        return CallOutcome(result, ref, record.response.get("cost_usd"), record.response.get("seconds"))
