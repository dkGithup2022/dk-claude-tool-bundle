"""SessionWriter: sessions/<세션>/session.json 쓰기."""

from __future__ import annotations

from abc import ABC, abstractmethod

from package.engine.model.session.claude_session import ClaudeSession


class SessionWriter(ABC):
    @abstractmethod
    def save_session(self, session: ClaudeSession) -> None: ...
