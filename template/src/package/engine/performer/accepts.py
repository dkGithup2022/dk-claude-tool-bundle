"""수행자가 받는 요청 종류 표."""

from __future__ import annotations

from package.engine.performer.performed_by import PerformedBy
from package.engine.request.code_request import CodeRequest
from package.engine.request.conversation_request import ConversationRequest
from package.engine.request.prompt_request import PromptRequest
from package.engine.request.question_request import QuestionRequest
from package.engine.request.show_request import ShowRequest
from package.engine.request.subagent_request import SubagentRequest
from package.engine.request.task_request import TaskRequest

# 수행자가 받는 요청 종류. create 때 작업의 request_type 과 맞는지 검사한다
ACCEPTS: dict[PerformedBy, type[TaskRequest]] = {
    PerformedBy.CODE: CodeRequest,
    PerformedBy.CLAUDE_P: PromptRequest,
    PerformedBy.MAIN_SESSION_SHOW: ShowRequest,
    PerformedBy.MAIN_SESSION_ASK: QuestionRequest,
    PerformedBy.MAIN_SESSION_TALK: ConversationRequest,
    PerformedBy.SUBAGENT: SubagentRequest,
}
