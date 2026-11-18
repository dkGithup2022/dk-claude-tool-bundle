"""SessionStart 훅: 세션을 열 때 대화 기록 경로를 적는다."""

from __future__ import annotations

from package.common.clock import utc_now
from package.engine.model.session.claude_session import ClaudeSession
from package.engine.port.session.session_reader import SessionReader
from package.engine.port.session.session_writer import SessionWriter


def on_session_start(sid: str, transcript_path: str | None, sessions: SessionReader, writer: SessionWriter) -> None:
    t = utc_now()
    session = sessions.load_session(sid) or ClaudeSession(sid, None, None, t, t)
    session.transcript_path, session.updated_at = transcript_path, t
    writer.save_session(session)
