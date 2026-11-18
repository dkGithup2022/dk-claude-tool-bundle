import json
import stat
from dataclasses import dataclass

import pytest

from package.claude_utils.prompt.call_prompt import call_prompt
from package.claude_utils.prompt.dto.prompt_spec import PromptSpec
from package.claude_utils.prompt.prompt_call_error import PromptCallError


@dataclass(frozen=True, slots=True)
class ExtractOutput:
    items: list[int]


def _fake_claude(tmp_path, monkeypatch, body: str):
    """claude 대신 도는 가짜 실행 파일."""
    exe = tmp_path / "fake-claude"
    exe.write_text("#!/bin/bash\n" + body)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PACKAGE_CLAUDE_BIN", str(exe))


def _spec(tmp_path, timeout_s=5):
    prompt = tmp_path / "p.md"
    prompt.write_text("# 작업\n일정을 뽑는다")
    return PromptSpec(name="extract", prompt_file=prompt, output_type=ExtractOutput, timeout_seconds=timeout_s)


def test_should_return_structured_output_and_record_when_claude_succeeds(tmp_path, monkeypatch):
    # given
    out = {"structured_output": {"items": [1]}, "total_cost_usd": 0.01, "num_turns": 1}
    _fake_claude(tmp_path, monkeypatch, f"cat > /dev/null\necho '{json.dumps(out)}'")
    # when
    result, record = call_prompt(_spec(tmp_path), "입력")
    # then
    assert result == ExtractOutput([1])
    assert record.request["user"] == "입력" and record.request["name"] == "extract"
    assert record.response["ok"] is True and record.response["cost_usd"] == 0.01


def test_should_raise_with_record_when_claude_reports_error(tmp_path, monkeypatch):
    _fake_claude(tmp_path, monkeypatch, 'echo \'{"is_error": true, "result": "bad", "total_cost_usd": 0.02}\'')
    with pytest.raises(PromptCallError) as e:
        call_prompt(_spec(tmp_path), "x")
    assert e.value.record.response["ok"] is False and e.value.record.response["cost_usd"] == 0.02


def test_should_kill_and_raise_with_record_when_claude_times_out(tmp_path, monkeypatch):
    _fake_claude(tmp_path, monkeypatch, "sleep 30")
    with pytest.raises(PromptCallError, match="시간 초과") as e:
        call_prompt(_spec(tmp_path, timeout_s=1), "x")
    assert e.value.record.response["error"] == "timeout"
