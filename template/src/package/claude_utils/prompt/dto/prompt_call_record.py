"""<노드 폴더>/calls/<n>/request.json, response.json"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PromptCallRecord:
    """<노드 폴더>/calls/<n>/request.json, response.json"""

    request: dict[str, Any]  # name, model, prompt_file, prompt_sha256, system, user, output_schema
    response: dict[str, Any]  # ok, exit_code, seconds, cost_usd, num_turns, structured_output, stdout, stderr
