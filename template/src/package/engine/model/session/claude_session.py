"""sessions/<session_id>/session.json"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ClaudeSession:
    """sessions/<session_id>/session.json"""

    session_id: str
    transcript_path: str | None  # SessionStart 훅이 적음
    active_run_id: str | None  # 진행 중인 실행. create 가 적고, 끝나거나 취소되면 비움
    created_at: str
    updated_at: str
