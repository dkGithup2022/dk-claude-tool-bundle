"""SessionReader: sessions/<세션>/session.json 읽기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.session.claude_session import ClaudeSession


class SessionReader(ABC):
    @abstractmethod
    def load_session(self, session_id: str) -> ClaudeSession | None:
        """없으면 None."""
