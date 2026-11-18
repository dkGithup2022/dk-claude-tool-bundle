"""default_performers: 수행자 6개를 PerformedBy 별로 묶는다 (메인 세션 판단은 아직 없음)."""

from __future__ import annotations

from package.engine.performer.claude_prompt.claude_prompt_performer import ClaudePromptPerformer
from package.engine.performer.code.code_performer import CodePerformer
from package.engine.performer.main_session.main_session_ask_performer import MainSessionAskPerformer
from package.engine.performer.main_session.main_session_show_performer import MainSessionShowPerformer
from package.engine.performer.main_session.main_session_talk_performer import MainSessionTalkPerformer
from package.engine.performer.performed_by import PerformedBy
from package.engine.performer.subagent.subagent_performer import SubagentPerformer
from package.engine.performer.task_performer import TaskPerformer
from package.engine.port.session.session_reader import SessionReader


def default_performers(session_reader: SessionReader) -> dict[PerformedBy, TaskPerformer]:
    items: list[TaskPerformer] = [
        CodePerformer(), ClaudePromptPerformer(), MainSessionShowPerformer(), MainSessionAskPerformer(),
        MainSessionTalkPerformer(session_reader), SubagentPerformer(),
    ]  # fmt: skip
    return {p.performed_by: p for p in items}
