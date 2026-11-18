"""새 실행기: demo 흐름(깊이 3)을 실제 수행자로 끝까지. 명령마다 실행기를 새로 만든다."""

import json
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from package.claude_utils.prompt.common.prompt_file import PromptFile
from package.claude_utils.prompt.dto.prompt_spec import PromptSpec
from package.common import files
from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.flow_definition import FlowDefinition
from package.engine.definition.ref import Ref
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.definition.unit.builders import group, task
from package.engine.hook.stop_hook import on_stop
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.run_state.flow_run_status import FlowRunStatus
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.model.session.claude_session import ClaudeSession
from package.engine.performer.default_performers import default_performers
from package.engine.performer.performed_by import PerformedBy
from package.engine.port.history.default_history_reader import DefaultHistoryReader
from package.engine.port.history.default_history_writer import DefaultHistoryWriter
from package.engine.port.result.default_result_reader import DefaultResultReader
from package.engine.port.result.default_result_writer import DefaultResultWriter
from package.engine.port.run_location import output_dir, run_dir
from package.engine.port.run_state.default_run_state_reader import DefaultRunStateReader
from package.engine.port.run_state.default_run_state_writer import DefaultRunStateWriter
from package.engine.port.session.default_session_reader import DefaultSessionReader
from package.engine.port.session.default_session_writer import DefaultSessionWriter
from package.engine.registry.registries import TASKS
from package.engine.request.code_request import CodeRequest
from package.engine.request.prompt_request import PromptRequest
from package.engine.request.question_request import QuestionRequest
from package.engine.request.show_request import ShowRequest
from package.engine.request.subagent_request import SubagentRequest
from package.engine.runner.child_run.child_run import ChildRun
from package.engine.runner.child_run.default_strategies import default_strategies
from package.engine.runner.flow.default_flow_runner import DefaultFlowRunner
from package.engine.runner.flow.dict_flow_registry import DictFlowRegistry
from package.engine.runner.unit.default_unit_runner import DefaultUnitRunner
from package.workflow.demo.demo_flow import DEMO_FLOW

SID = "sess-v2"
FLOWS: dict[str, FlowDefinition] = {"demo": DEMO_FLOW}


def runner() -> DefaultFlowRunner:
    sessions = DefaultSessionReader()
    performers = default_performers(sessions)
    unit = DefaultUnitRunner(DefaultRunStateWriter(), DefaultHistoryWriter(), DefaultResultReader(),
                             DefaultResultWriter(), performers, default_strategies())  # fmt: skip
    return DefaultFlowRunner(DictFlowRegistry(FLOWS), sessions, DefaultSessionWriter(), DefaultRunStateReader(),
                             DefaultRunStateWriter(), unit, performers)  # fmt: skip


def session() -> ClaudeSession:
    s = DefaultSessionReader().load_session(SID)
    if s is None:
        s = ClaudeSession(SID, "/tmp/t.jsonl", None, "t0", "t0")
        DefaultSessionWriter().save_session(s)
    return s


def kinds(ins) -> tuple[str, str]:
    p = ins.payload
    return ins.type.value, getattr(p, "question", None) or getattr(p, "text", None) or getattr(p, "opening", "")


def _last_run() -> str:
    """가장 최근 실행 id (끝났거나 취소돼 active_run_id 가 비었을 때도)."""
    return sorted(p.name for p in run_dir(SID, "x").parent.iterdir())[-1]


def state():
    return DefaultRunStateReader().load_run(SID, _last_run())


def test_should_walk_demo_to_finished_and_record_files():
    # when
    seen = [kinds(runner().start(session(), "demo"))]
    seen.append(kinds(runner().next_instruction(session())))
    for answer in [None, "예", "맞음", "아님"]:
        seen.append(kinds(runner().submit_reply(session(), answer)))
    seen.append(kinds(runner().next_instruction(session())))
    # then
    assert seen == [
        ("show", "가짜 흐름을 시작합니다."), ("talk", "좋아하는 과일이 뭐예요?"), ("ask", "과일마다 확인할까요?"),
        ("ask", "사과 맞나요?"), ("ask", "배 맞나요?"), ("show", "가짜 흐름이 끝났습니다."),
        ("finished", "끝났습니다."),
    ]  # fmt: skip
    st = DefaultRunStateReader().load_run(SID, _last_run())
    assert st.status is FlowRunStatus.FINISHED and st.waiting_instruction is None
    assert DefaultSessionReader().load_session(SID).active_run_id is None
    each = st.scenario.children[2].children[1]
    q = each.children[0]
    assert each.item_count == 2 and q.done_items == ["1", "2"]
    d = run_dir(SID, st.run_id)
    answers = {"1": {"answer": "맞음"}, "2": {"answer": "아님"}}
    assert files.read_json(d / q.folder_name / "result.json") == {"by_item": answers}
    assert files.read_json(d / each.folder_name / "items.json")["items"] == ["사과", "배"]
    rows = files.read_jsonl(d / "history.jsonl")
    hist = [(h["node_folder"].rsplit("_", 1)[0], h["item_key"], h["status"]) for h in rows]
    assert hist == [
        ("hello", None, "completed"), ("listen", None, "waiting"), ("listen", None, "completed"),
        ("collect_fruits", None, "completed"), ("ask_check", None, "waiting"), ("ask_check", None, "completed"),
        ("confirm", "1", "waiting"), ("confirm", "1", "completed"), ("confirm", "2", "waiting"),
        ("confirm", "2", "completed"), ("bye", None, "completed"),
    ]  # fmt: skip
    talk = files.read_json(d / st.scenario.children[1].children[0].folder_name / "result.json")["by_item"]["-"]
    assert talk["transcript"] == "/tmp/t.jsonl" and talk["from"] == st.created_at


def test_should_repeat_same_instruction_and_refuse_reply_without_waiting():
    runner().start(session(), "demo")  # show
    assert runner().submit_reply(session(), "예").type is InstructionType.FAILED  # 기다리는 지시 없음
    talk = runner().next_instruction(session())
    assert runner().next_instruction(session()) == talk


def test_should_ask_again_when_answer_is_empty_or_outside_choices():
    runner().start(session(), "demo")
    runner().next_instruction(session())
    ask = runner().submit_reply(session(), None)
    assert runner().submit_reply(session(), "") == ask
    assert runner().submit_reply(session(), "응") == ask
    notes = [h.note for h in DefaultHistoryReader().read_history(state()) if h.note]
    assert notes == ["다시 물음: 빈 답 ('')", "다시 물음: 선택지 밖의 답: 응 ('응')"]


def test_should_skip_items_when_user_says_no():
    runner().start(session(), "demo")
    runner().next_instruction(session())
    runner().submit_reply(session(), None)
    bye = runner().submit_reply(session(), "아니요")
    assert kinds(bye) == ("show", "가짜 흐름이 끝났습니다.")
    each = state().scenario.children[2].children[1]
    assert each.status is NodeStatus.SKIPPED


def test_should_stop_answering_when_cancelled():
    runner().start(session(), "demo")
    runner().cancel(session())
    assert runner().next_instruction(session()).type is InstructionType.FAILED  # 진행 중인 실행 없음


# ---- 실패와 다시, spawn, claude -p ----

CALLS = {"n": 0}


@TASKS.register_as("test_v2.flaky")
class _Flaky(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        CALLS["n"] += 1
        if CALLS["n"] == 1:
            raise TimeoutError("잠깐 실패")
        return TaskOutput({"ok": True})


@TASKS.register_as("test_v2.spawn")
class _Spawn(Task):
    request_type = SubagentRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> SubagentRequest:
        return SubagentRequest("package:prep-writer", f"결과 폴더: {context.output_dir()}")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput()


@TASKS.register_as("test_v2.spawn_strict")
class _SpawnStrict(_Spawn):
    """파일이 꼭 있어야 하는 작업은 Task 가 직접 확인한다."""

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        if not any(context.output_dir().iterdir()):
            raise FileNotFoundError("산출물이 없습니다")
        return TaskOutput()


@dataclass(frozen=True, slots=True)
class _AnyOutput:
    text: str


@TASKS.register_as("test_v2.prompt")
class _Prompt(Task):
    request_type = PromptRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> PromptRequest:
        p = Path(__file__).parent / "p.md"
        return PromptRequest(PromptSpec("t", p if p.exists() else Path(__file__), _AnyOutput), "입력")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({"text": result.text})


def _one(name: str, performed_by: PerformedBy, key: str) -> None:
    FLOWS[name] = FlowDefinition(name, "시험", group("root", ChildRun.IN_ORDER, task("only", performed_by, Ref(key))))


def test_should_fail_then_retry_same_node_and_keep_active_run():
    CALLS["n"] = 0
    _one("flaky", PerformedBy.CODE, "test_v2.flaky")
    first = runner().start(session(), "flaky")
    st = state()
    assert first.type is InstructionType.FAILED and "잠깐 실패" in first.payload.text
    assert st.status is FlowRunStatus.FAILED and DefaultSessionReader().load_session(SID).active_run_id == st.run_id
    assert runner().next_instruction(session()).type is InstructionType.FINISHED and CALLS["n"] == 2


def test_should_collect_files_written_by_subagent_when_done():
    # given: 서브에이전트 단계 하나
    _one("sp", PerformedBy.SUBAGENT, "test_v2.spawn")
    spawn = runner().start(session(), "sp")
    stop_while_spawned = on_stop(SID, {"session_id": SID}, DefaultSessionReader(), DefaultRunStateReader())
    node = state().scenario.children[0]
    folder = output_dir(state(), node, "-")
    # when: 서브에이전트 대신 산출물 폴더에 파일 둘을 쓰고 done
    (folder / "aa.md").write_text("# A")
    (folder / "bb.md").write_text("# B")
    done = runner().submit_reply(session(), None)
    # then: 폴더에 생긴 파일 전부가 결과
    assert spawn.type is InstructionType.SPAWN and spawn.payload.message == f"결과 폴더: {folder}"
    assert done.type is InstructionType.FINISHED and stop_while_spawned["decision"] == "block"
    result = files.read_json(run_dir(SID, state().run_id) / node.folder_name / "result.json")
    assert result == {"by_item": {"-": {"files": ["aa.md", "bb.md"]}}}


def test_should_finish_with_warning_when_output_folder_is_empty():
    _one("sp", PerformedBy.SUBAGENT, "test_v2.spawn")
    runner().start(session(), "sp")
    done = runner().submit_reply(session(), None)
    notes = [h.note for h in DefaultHistoryReader().read_history(state()) if h.note]
    assert done.type is InstructionType.FINISHED and notes == ["경고: 산출물 폴더가 비어 있음"]


@dataclass(frozen=True, slots=True)
class _DocsOutput:
    files: list[PromptFile]


@TASKS.register_as("test_v2.prompt_docs")
class _PromptDocs(Task):
    request_type = PromptRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> PromptRequest:
        return PromptRequest(PromptSpec("docs", Path(__file__), _DocsOutput), "입력")

    def build_output(self, context: FlowContext, result: _DocsOutput) -> TaskOutput:
        return TaskOutput(files={f.name: f.content for f in result.files})


@TASKS.register_as("test_v2.show_docs")
class _ShowDocs(Task):
    request_type = ShowRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ShowRequest:
        return ShowRequest(" | ".join(f"{k}={v}" for k, v in context.read("docs").items()))

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput()


def test_should_write_prompt_files_and_let_next_step_read_them(tmp_path, monkeypatch):
    # given: claude -p 가 파일 둘을 돌려주고, 다음 단계가 그것을 읽어 보인다
    out = {"structured_output": {"files": [{"name": "aa.md", "content": "# A"}, {"name": "bb.md", "content": "# B"}]}}
    exe = tmp_path / "claude"
    exe.write_text(f"#!/bin/bash\ncat >/dev/null\necho '{json.dumps(out)}'\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PACKAGE_CLAUDE_BIN", str(exe))
    FLOWS["docs"] = FlowDefinition("docs", "시험", group("root", ChildRun.IN_ORDER,
        task("docs", PerformedBy.CLAUDE_P, Ref("test_v2.prompt_docs")),
        task("show", PerformedBy.MAIN_SESSION_SHOW, Ref("test_v2.show_docs"), reads=("docs",))))  # fmt: skip
    # when
    show = runner().start(session(), "docs")
    # then
    assert show.payload.text == "aa.md=# A | bb.md=# B"
    assert (output_dir(state(), state().scenario.children[0], "-") / "bb.md").read_text() == "# B"


@TASKS.register_as("test_v2.wrong_kind")
class _WrongKind(_Flaky):
    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput(files={"a.md": "x"})


def test_should_fail_when_output_does_not_match_declared_kind():
    _one("wk", PerformedBy.CODE, "test_v2.wrong_kind")
    failed = runner().start(session(), "wk")
    assert failed.type is InstructionType.FAILED and "결과 종류가 data 인데" in failed.payload.text


def test_should_record_failed_prompt_call_cost(tmp_path, monkeypatch):
    exe = tmp_path / "claude"
    body = '{"is_error": true, "result": "bad", "total_cost_usd": 0.02}'
    exe.write_text(f"#!/bin/bash\ncat >/dev/null\necho '{body}'\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PACKAGE_CLAUDE_BIN", str(exe))
    _one("pr", PerformedBy.CLAUDE_P, "test_v2.prompt")
    failed = runner().start(session(), "pr")
    h = [x for x in DefaultHistoryReader().read_history(state()) if x.status is NodeStatus.FAILED][0]
    assert failed.type is InstructionType.FAILED
    assert h.call_files == (f"{h.node_folder}/calls/1",) and h.cost_usd == 0.02
    call = run_dir(SID, state().run_id) / h.node_folder / "calls" / "1" / "response.json"
    assert json.loads(call.read_text())["ok"] is False


def test_should_not_start_when_definition_has_problems():
    _one("bad", PerformedBy.CLAUDE_P, "test_v2.flaky")  # CODE 작업에 CLAUDE_P
    ins = runner().start(session(), "bad")
    assert ins.type is InstructionType.FAILED
    assert "PromptRequest 를 받는데 test_v2.flaky 는 CodeRequest" in ins.payload.text
    assert DefaultSessionReader().load_session(SID).active_run_id is None


@pytest.fixture(autouse=True)
def _clean_flows():
    yield
    for k in [k for k in FLOWS if k != "demo"]:
        del FLOWS[k]


# ---- 반복 안의 반복, 건너뜀, 실패 뒤 회복의 디스크 상태 ----

ITEMS = {"outer": [{"name": "a", "inner": ["x", "y"]}, {"name": "b", "inner": ["z"]}]}


@TASKS.register_as("test_v2.ask_inner")
class _AskInner(Task):
    request_type = QuestionRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest(f"{context.item_key} {context.current_item()}", ("ok",))

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({"answer": result})


def _register_nested() -> None:
    from package.engine.registry.registries import CONDITIONS, ITEM_SOURCES

    if not ITEM_SOURCES.has("test_v2.outer"):
        ITEM_SOURCES.register("test_v2.outer", lambda: lambda ctx: ITEMS["outer"])
        ITEM_SOURCES.register("test_v2.inner", lambda: lambda ctx: ctx.current_item()["inner"])
        CONDITIONS.register("test_v2.not_y", lambda: lambda ctx: ctx.current_item() != "y")


def test_should_walk_nested_loops_with_skip_and_record_keys():
    # given: 바깥 2개 × 안쪽 2개/1개, 안쪽 "y" 는 건너뜀
    _register_nested()
    FLOWS["nested"] = FlowDefinition("nested", "시험", group("root", ChildRun.IN_ORDER,
        group("outer", ChildRun.FOR_EACH_ITEM,
              group("inner", ChildRun.FOR_EACH_ITEM,
                    task("q", PerformedBy.MAIN_SESSION_ASK, Ref("test_v2.ask_inner"), run_if=Ref("test_v2.not_y")),
                    for_each_item_in=Ref("test_v2.inner")),
              for_each_item_in=Ref("test_v2.outer"))))  # fmt: skip
    # when
    seen = [runner().start(session(), "nested").payload.question]
    seen.append(runner().submit_reply(session(), "ok").payload.question)
    last = runner().submit_reply(session(), "ok")
    # then
    assert seen[:2] == ["1.1 x", "2.1 z"] and last.type is InstructionType.FINISHED
    st = state()
    q = st.scenario.children[0].children[0].children[0]
    assert q.done_items == ["1.1", "1.2", "2.1"] and q.status is NodeStatus.COMPLETED
    assert st.scenario.children[0].status is NodeStatus.COMPLETED
    skipped = [h.item_key for h in DefaultHistoryReader().read_history(st) if h.status is NodeStatus.SKIPPED]
    assert skipped == ["1.2"]


def test_should_save_running_status_after_recovering_from_failed_reply():
    # given: 서브에이전트 다음에 질문이 있는 흐름. 산출물 없이 done → 작업이 실패를 냄
    FLOWS["sp_ask"] = FlowDefinition("sp_ask", "시험", group("root", ChildRun.IN_ORDER,
        task("write", PerformedBy.SUBAGENT, Ref("test_v2.spawn_strict")),
        task("q", PerformedBy.MAIN_SESSION_ASK, Ref("test_v2.ask_inner"))))  # fmt: skip
    runner().start(session(), "sp_ask")
    assert runner().submit_reply(session(), None).type is InstructionType.FAILED
    # when: 파일을 만들고 바로 done (next 없이)
    (output_dir(state(), state().scenario.children[0], "-") / "prep.md").write_text("메모")
    ask = runner().submit_reply(session(), None)
    # then: 다음 질문을 기다리는 동안 디스크의 실행 상태는 running
    assert ask.type is InstructionType.ASK and state().status is FlowRunStatus.RUNNING
