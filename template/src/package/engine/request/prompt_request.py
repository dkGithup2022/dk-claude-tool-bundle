"""CLAUDE_P 가 받음 → 결과: dict."""

from __future__ import annotations

from dataclasses import dataclass

from package.claude_utils.prompt.dto.prompt_spec import PromptSpec


@dataclass(frozen=True, slots=True)
class PromptRequest:
    """CLAUDE_P 가 받음 → 결과: dict."""

    spec: PromptSpec
    input_text: str
