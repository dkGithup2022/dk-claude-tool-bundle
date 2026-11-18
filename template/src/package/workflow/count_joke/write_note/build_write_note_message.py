"""write_note 가 서브에이전트에게 넘길 메시지."""

from __future__ import annotations

from pathlib import Path


def build_write_note_message(count: int, joke: str, output_dir: Path) -> str:
    return "\n".join(
        [
            f"숫자: {count}",
            f"말장난: {joke}",
            f"결과 폴더: {output_dir}",
        ]
    )
