"""DefaultSessionReader: 세션 파일을 읽는다."""

from __future__ import annotations

from package.common import files
from package.engine.model.session.claude_session import ClaudeSession
from package.engine.port.run_location import session_dir
from package.engine.port.session.session_file_converter import SessionFileConverter
from package.engine.port.session.session_reader import SessionReader


class DefaultSessionReader(SessionReader):
    def load_session(self, session_id: str) -> ClaudeSession | None:
        p = session_dir(session_id) / "session.json"
        return SessionFileConverter().to_data(files.read_json(p)) if p.exists() else None
