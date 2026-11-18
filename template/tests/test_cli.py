"""CLI 와 훅: 새 실행기로 demo 흐름. 명령마다 새 프로세스처럼 main() 을 부른다."""

import io
import json
import sys

from package.engine.port.session.default_session_reader import DefaultSessionReader
from package.entry import cli

SID = "sess-cli"


def run(*args: str) -> dict:
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    try:
        cli.main(["--session", SID, *args])
    finally:
        sys.stdout = old
    return json.loads(out.getvalue()) if out.getvalue().strip() else {}


def hook(event: str, data: dict) -> dict:
    old_in = sys.stdin
    sys.stdin = io.StringIO(json.dumps(data))
    try:
        return run("hook", event)
    finally:
        sys.stdin = old_in


def test_should_run_demo_through_cli_with_payload_json():
    hook("session-start", {"session_id": SID, "transcript_path": "/t.jsonl"})
    first = run("start", "demo")
    assert first["type"] == "show" and first["payload"] == {"text": "가짜 흐름을 시작합니다."}
    talk = run("next")
    assert talk["type"] == "talk" and talk["payload"]["opening"] == "좋아하는 과일이 뭐예요?"
    ask = run("done")
    assert ask["type"] == "ask" and ask["payload"]["choices"] == ["예", "아니요"]
    assert run("done", "--answer", "아니요")["type"] == "show"
    assert run("next")["type"] == "finished"
    assert run("status") == {"status": "none"}


def test_should_block_stop_only_for_owner_session_when_next_is_due():
    hook("session-start", {"session_id": SID})
    run("start", "demo")  # show 뒤: 기다리는 지시 없음 → next 차례
    assert hook("stop", {"session_id": SID})["decision"] == "block"
    assert hook("stop", {"session_id": SID, "stop_hook_active": True}) == {}
    assert hook("stop", {"session_id": "other"}) == {}
    run("next")  # talk 를 기다림 → 막지 않음
    assert hook("stop", {"session_id": SID}) == {}


def test_should_let_stop_when_run_failed():
    hook("session-start", {"session_id": SID})
    assert run("start", "nope")["type"] == "failed"  # 모르는 흐름: 실행이 없음
    assert hook("stop", {"session_id": SID}) == {}


def test_should_record_transcript_path_when_session_starts():

    hook("session-start", {"session_id": SID, "transcript_path": "/x.jsonl"})
    assert DefaultSessionReader().load_session(SID).transcript_path == "/x.jsonl"
