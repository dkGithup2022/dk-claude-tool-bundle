"""SessionFileConverter: ClaudeSession ↔ session.json."""

from __future__ import annotations

from typing import Any

from package.engine.model.session.claude_session import ClaudeSession


class SessionFileConverter:
    def to_file(self, s: ClaudeSession) -> dict[str, Any]:
        return {"session_id": s.session_id, "transcript_path": s.transcript_path, "active_run_id": s.active_run_id,
                "created_at": s.created_at, "updated_at": s.updated_at}  # fmt: skip

    def to_data(self, d: dict[str, Any]) -> ClaudeSession:
        return ClaudeSession(d["session_id"], d.get("transcript_path"), d.get("active_run_id"), d["created_at"],
                             d["updated_at"])  # fmt: skip
