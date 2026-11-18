"""TaskRequest: 작업이 수행자에게 넘기는 요청의 모든 종류."""

from __future__ import annotations

from package.engine.request.code_request import CodeRequest
from package.engine.request.conversation_request import ConversationRequest
from package.engine.request.prompt_request import PromptRequest
from package.engine.request.question_request import QuestionRequest
from package.engine.request.show_request import ShowRequest
from package.engine.request.subagent_request import SubagentRequest

TaskRequest = CodeRequest | ShowRequest | PromptRequest | QuestionRequest | ConversationRequest | SubagentRequest
