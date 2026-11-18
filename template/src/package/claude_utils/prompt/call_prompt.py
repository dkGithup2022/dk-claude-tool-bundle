"""claude -p 관문. 모든 프롬프트 호출은 PromptSpec 으로 여기서만 실행한다. 호출 기록(PromptCallRecord)을 돌려준다.

빈 임시 폴더에서, 도구 없이, 프로젝트 설정만 읽게 해
이 플러그인의 훅이 자식 안에서 돌지 않게 한다. 요금제로 돌도록 ANTHROPIC_API_KEY 를 지운다.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord
from package.claude_utils.prompt.dto.prompt_spec import PromptSpec
from package.claude_utils.prompt.prompt_call_error import PromptCallError
from package.claude_utils.prompt.prompt_output_converter import PromptOutputConverter


def call_prompt(spec: PromptSpec, user_input: str) -> tuple[Any, PromptCallRecord]:
    """claude -p 를 한 번 부른다. 성공하면 (출력 데이터 클래스 객체, 호출 기록), 실패하면 PromptCallError."""
    converter = PromptOutputConverter()
    schema = converter.to_schema(spec.output_type)
    ok, request, response, result, message = _invoke(
        spec.name, spec.prompt_file, schema, spec.model, spec.timeout_seconds, user_input
    )
    record = PromptCallRecord(request, response)
    if not ok:
        raise PromptCallError(message, record)
    try:
        return converter.to_data(spec.output_type, result), record
    except (KeyError, TypeError) as e:
        raise PromptCallError(f"출력이 {spec.output_type.__name__} 모양이 아님: {e}", record) from e


def _invoke(
    name: str, prompt_file: Path, output_schema: dict[str, Any], model: str, timeout_s: int, user_input: str
) -> tuple[bool, dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """(성공, 요청 기록, 응답 기록, 결과, 실패 글)."""
    system = prompt_file.read_text(encoding="utf-8")
    argv = [
        os.environ.get("PACKAGE_CLAUDE_BIN", "claude"), "-p", "--model", model,
        "--output-format", "json", "--json-schema", json.dumps(output_schema, ensure_ascii=False),
        "--system-prompt", system, "--tools", "", "--setting-sources", "project", "--no-session-persistence",
    ]  # fmt: skip
    request = {
        "name": name, "model": model, "timeout_s": timeout_s, "prompt_file": str(prompt_file),
        "prompt_sha256": hashlib.sha256(system.encode()).hexdigest(), "system": system, "user": user_input,
        "output_schema": output_schema,
    }  # fmt: skip
    started = time.monotonic()
    timed_out, out, err, code = _run(argv, user_input, timeout_s)
    seconds = round(time.monotonic() - started, 2)
    if timed_out:
        response = {"ok": False, "exit_code": None, "seconds": seconds, "error": "timeout"}
        return False, request, response, {}, f"claude 시간 초과 ({timeout_s}초)"
    parsed: Any = None
    with contextlib.suppress(ValueError):
        parsed = json.loads(out)
    p = parsed if isinstance(parsed, dict) else {}
    ok = code == 0 and bool(p) and not p.get("is_error") and "structured_output" in p
    response = {
        "ok": ok, "exit_code": code, "seconds": seconds, "cost_usd": p.get("total_cost_usd"),
        "num_turns": p.get("num_turns"), "structured_output": p.get("structured_output"), "stdout": out, "stderr": err,
    }  # fmt: skip
    message = "" if ok else f"claude 실패 (exit {code}): {(err or out)[:300]}"
    return ok, request, response, (p["structured_output"] if ok else {}), message


def _run(argv: list[str], user_input: str, timeout_s: int) -> tuple[bool, str, str, int]:
    """새 프로세스 그룹으로 띄우고, 시간이 넘으면 그룹째 끝낸다. (시간 초과, stdout, stderr, 종료 코드)."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with tempfile.TemporaryDirectory(prefix="package-") as cwd:
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, cwd=cwd, env=env, start_new_session=True)  # fmt: skip
        try:
            out, err = p.communicate(user_input, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return True, "", "", -1
    return False, out or "", err or "", p.returncode
