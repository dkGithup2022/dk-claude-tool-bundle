"""호출 기록을 노드 폴더에 저장한 뒤의 claude -p 실패. 저장 위치·비용·시간만 담고, 실행기가 history 에 남긴다."""

from __future__ import annotations


class RecordedPromptCallError(RuntimeError):
    """호출 기록을 노드 폴더에 저장한 뒤의 claude -p 실패. 저장 위치·비용·시간만 담고, 실행기가 history 에 남긴다."""

    def __init__(self, message: str, call_file: str, cost_usd: float | None, seconds: float | None) -> None:
        super().__init__(message)
        self.call_file, self.cost_usd, self.seconds = call_file, cost_usd, seconds
