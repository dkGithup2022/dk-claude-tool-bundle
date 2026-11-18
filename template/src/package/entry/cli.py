"""package 명령. 인자 해석, 실행기 조립, JSON 출력만."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from package.common.clock import utc_now
from package.engine.hook.session_start_hook import on_session_start
from package.engine.hook.stop_hook import on_stop
from package.engine.instruction.instruction_converter import InstructionConverter
from package.engine.model.session.claude_session import ClaudeSession
from package.engine.performer.default_performers import default_performers
from package.engine.port.history.default_history_writer import DefaultHistoryWriter
from package.engine.port.result.default_result_reader import DefaultResultReader
from package.engine.port.result.default_result_writer import DefaultResultWriter
from package.engine.port.run_state.default_run_state_reader import DefaultRunStateReader
from package.engine.port.run_state.default_run_state_writer import DefaultRunStateWriter
from package.engine.port.run_state.run_state_file_converter import RunStateFileConverter
from package.engine.port.session.default_session_reader import DefaultSessionReader
from package.engine.port.session.default_session_writer import DefaultSessionWriter
from package.engine.runner.child_run.default_strategies import default_strategies
from package.engine.runner.flow.default_flow_runner import DefaultFlowRunner
from package.engine.runner.flow.dict_flow_registry import DictFlowRegistry
from package.engine.runner.unit.default_unit_runner import DefaultUnitRunner
from package.workflow.registry import FLOWS


def build_runner() -> DefaultFlowRunner:
    sessions, runs = DefaultSessionReader(), DefaultRunStateReader()
    performers = default_performers(sessions)
    unit = DefaultUnitRunner(DefaultRunStateWriter(), DefaultHistoryWriter(), DefaultResultReader(),
                             DefaultResultWriter(), performers, default_strategies())  # fmt: skip
    return DefaultFlowRunner(DictFlowRegistry(FLOWS), sessions, DefaultSessionWriter(), runs, DefaultRunStateWriter(),
                             unit, performers)  # fmt: skip


def hook(event: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Claude Code 훅. 세션을 열 때 대화 기록 경로를 적고, 멈추려 할 때 할 일이 남았으면 막는다."""
    if data.get("cwd"):
        os.chdir(data["cwd"])
    sid = str(data.get("session_id") or "")
    if not sid:
        return None
    if event == "session-start":
        on_session_start(sid, data.get("transcript_path"), DefaultSessionReader(), DefaultSessionWriter())
        return None
    return on_stop(sid, data, DefaultSessionReader(), DefaultRunStateReader())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="package")
    p.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID", "no-session"))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("flow")
    sub.add_parser("next")
    d = sub.add_parser("done")
    d.add_argument("--answer")
    sub.add_parser("status")
    sub.add_parser("cancel")
    h = sub.add_parser("hook")
    h.add_argument("event", choices=["session-start", "stop"])
    a = p.parse_args(argv)

    if a.cmd == "hook":
        out = hook(a.event, json.loads(sys.stdin.read() or "{}"))
        if out:
            print(json.dumps(out, ensure_ascii=False))
        return 0
    runner, instructions = build_runner(), InstructionConverter()
    session = _session(a.session)
    if a.cmd == "start":
        return _print(instructions.to_json(runner.start(session, a.flow)))
    if a.cmd == "next":
        return _print(instructions.to_json(runner.next_instruction(session)))
    if a.cmd == "done":
        return _print(instructions.to_json(runner.submit_reply(session, a.answer)))
    if a.cmd == "status":
        state = runner.read_state(session)
        return _print(RunStateFileConverter().to_file(state) if state else {"status": "none"})
    return _print(instructions.to_json(runner.cancel(session)))


def _session(session_id: str) -> ClaudeSession:
    """세션 파일이 없으면(훅이 돌지 않음) 대화 기록 경로 없이 만든다."""
    found = DefaultSessionReader().load_session(session_id)
    if found is not None:
        return found
    t = utc_now()
    session = ClaudeSession(session_id, None, None, t, t)
    DefaultSessionWriter().save_session(session)
    return session


def _print(obj: dict[str, Any]) -> int:
    print(json.dumps(obj, ensure_ascii=False))
    return 0
