import pytest

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.ref import Ref
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task import Task
from package.engine.definition.task.task_output import TaskOutput
from package.engine.definition.unit.builders import group, task
from package.engine.model.run_state.node_kind import NodeKind
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.performer.performed_by import PerformedBy
from package.engine.port.result.default_result_writer import DefaultResultWriter
from package.engine.registry.registries import CONDITIONS, ITEM_SOURCES, TASKS
from package.engine.request.code_request import CodeRequest
from package.engine.request.question_request import QuestionRequest
from package.engine.runner.child_run.child_run import ChildRun
from package.engine.runner.scenario.build_scenario import build_scenario
from package.engine.runner.scenario.check_definition import check_definition

ALL = list(PerformedBy)


@TASKS.register_as("test_def.ask")
class _Ask(Task):
    request_type = QuestionRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest("q", ("a", "b"))

    def build_output(self, context: FlowContext, result: object) -> TaskOutput:
        return TaskOutput({"answer": result})


@TASKS.register_as("test_def.no_type")
class _NoType(Task):
    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest("q", ("a",))

    def build_output(self, context: FlowContext, result: object) -> TaskOutput:
        return TaskOutput({})


@TASKS.register_as("test_def.files")
class _Files(Task):
    request_type = CodeRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: object) -> TaskOutput:
        return TaskOutput(files={"a.md": "# A"})


TASKS.register("test_def.ask2", _Ask)
CONDITIONS.register("test_def.always", lambda: lambda ctx: True)
ITEM_SOURCES.register("test_def.items", lambda: lambda ctx: [1, 2])


def test_should_reject_bad_assembly_when_unit_is_built():
    ask = task("a", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask"))
    with pytest.raises(ValueError, match="영문 소문자"):
        task("Bad Name", PerformedBy.CODE, Ref("x"))
    with pytest.raises(ValueError, match="for_each_item_in"):
        group("g", ChildRun.FOR_EACH_ITEM, ask)
    with pytest.raises(ValueError, match="겹친다"):
        group("g", ChildRun.IN_ORDER, ask, ask)
    with pytest.raises(ValueError, match="자식이 없다"):
        group("g", ChildRun.IN_ORDER)


def test_should_list_problems_before_start_when_refs_or_pairs_are_wrong():
    # given
    root = group("root", ChildRun.IN_ORDER,
        task("ok", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask"), run_if=Ref("test_def.always")),
        task("wrong_pair", PerformedBy.CLAUDE_P, Ref("test_def.ask")),
        task("no_type", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.no_type")),
        task("missing", PerformedBy.CODE, Ref("test_def.nope"), run_if=Ref("test_def.nope_cond")),
        group("each", ChildRun.FOR_EACH_ITEM, task("x", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask")),
              for_each_item_in=Ref("test_def.nope_items")),
    )  # fmt: skip
    # when
    problems = check_definition(root, [p for p in ALL if p is not PerformedBy.MAIN_SESSION_ASK] + [])
    problems_all = check_definition(root, ALL)
    # then
    assert any("ok: 수행자가 없는 main_session_ask" in p for p in problems)
    assert problems_all == [
        "wrong_pair: claude_p 는 PromptRequest 를 받는데 test_def.ask 는 QuestionRequest",
        "no_type: main_session_ask 는 QuestionRequest 를 받는데 test_def.no_type 는 request_type 없음",
        "no_type: test_def.no_type 에 output_kind 가 없다",
        "missing: 등록되지 않은 조건 test_def.nope_cond",
        "missing: 등록되지 않은 작업 test_def.nope",
        "each: 등록되지 않은 반복 항목 test_def.nope_items",
        "같은 작업을 두 번 쓴다: test_def.ask",
    ]


def test_should_list_name_and_reads_problems_before_start():
    # given: 이름 겹침, 뒤에 실행되는 노드 읽기, 묶음 읽기, 없는 노드 읽기
    root = group("root", ChildRun.IN_ORDER,
        task("first", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask"), reads=("second", "grp", "ghost")),
        task("second", PerformedBy.CODE, Ref("test_def.files")),
        group("grp", ChildRun.IN_ORDER, task("first", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask2"))),
    )  # fmt: skip
    # when / then
    assert check_definition(root, ALL) == [
        "노드 이름이 겹친다: first",
        "first: reads 의 노드가 먼저 실행되지 않는다: second",
        "first: reads 의 노드가 작업이 아니다: grp",
        "first: reads 의 노드가 없다: ghost",
    ]


def test_should_copy_definition_into_scenario_with_uuids():
    root = group("root", ChildRun.IN_ORDER,
        group("each", ChildRun.FOR_EACH_ITEM, task("x", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask")),
              for_each_item_in=Ref("test_def.items"), run_if=Ref("test_def.always")))  # fmt: skip
    s = build_scenario(root)
    each, x = s.children[0], s.children[0].children[0]
    assert (s.kind, each.child_run, each.for_each_item_in, each.run_if) == (
        NodeKind.GROUP,
        ChildRun.FOR_EACH_ITEM,
        Ref("test_def.items"),
        Ref("test_def.always"),
    )
    assert (x.kind, x.performed_by, x.task, x.status) == (
        NodeKind.TASK,
        PerformedBy.MAIN_SESSION_ASK,
        Ref("test_def.ask"),
        NodeStatus.PENDING,
    )
    assert len({s.uuid, each.uuid, x.uuid}) == 3


def test_should_reject_duplicate_and_unknown_keys_in_registry():
    with pytest.raises(ValueError, match="겹친다"):
        TASKS.register("test_def.ask", _Ask)
    with pytest.raises(KeyError, match="등록되지 않은 작업"):
        TASKS.create(Ref("test_def.unknown"))


def test_should_read_previous_output_by_node_name_with_default_item_key():
    from package.engine.definition.task.output_missing_error import OutputMissingError
    from package.engine.model.run_state.flow_run_state import FlowRunState
    from package.engine.model.run_state.flow_run_status import FlowRunStatus
    from package.engine.port.result.default_result_reader import DefaultResultReader

    # given: root → extract(반복 밖), doc(파일 결과), outer(반복) → pick, inner(반복) → q, r(앞 결과를 읽음)
    root = build_scenario(group("root", ChildRun.IN_ORDER,
        task("extract", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask")),
        task("doc", PerformedBy.CODE, Ref("test_def.files")),
        group("outer", ChildRun.FOR_EACH_ITEM,
              task("pick", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask")),
              group("inner", ChildRun.FOR_EACH_ITEM,
                    task("q", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask")),
                    task("r", PerformedBy.MAIN_SESSION_ASK, Ref("test_def.ask"),
                         reads=("extract", "doc", "pick", "q")),
                    for_each_item_in=Ref("test_def.items")),
              for_each_item_in=Ref("test_def.items"))))  # fmt: skip
    st = FlowRunState("r_1", "t", "s", FlowRunStatus.RUNNING, "t0", "t0", root, None)
    extract, doc, outer = root.children
    pick, q, r = outer.children[0], outer.children[1].children[0], outer.children[1].children[1]
    w = DefaultResultWriter()
    w.save_result(st, extract, "-", TaskOutput({"items": [1, 2]}))
    w.save_result(st, doc, "-", TaskOutput({"files": w.save_files(st, doc, "-", {"a.md": "# A", "sub/b.md": "# B"})}))
    w.save_result(st, pick, "2", TaskOutput({"answer": "b"}))
    w.save_result(st, q, "2.1", TaskOutput({"answer": "c"}))
    ctx = FlowContext(st, r, "2.3", DefaultResultReader(), w)
    # when / then: 반복 밖은 "-", 바깥 반복 안은 "2", 같은 깊이는 지정한 키. 파일 결과는 이름 → 내용
    assert ctx.read("extract") == {"items": [1, 2]}
    assert ctx.read("doc") == {"a.md": "# A", "sub/b.md": "# B"}
    assert ctx.read("pick") == {"answer": "b"}
    assert ctx.read("q", "2.1") == {"answer": "c"}
    with pytest.raises(OutputMissingError):
        ctx.read("q")  # 2.3 은 아직 없음
    with pytest.raises(ValueError, match="reads 에 없는 노드"):
        ctx.read("outer")
    with pytest.raises(ValueError, match="산출물 폴더 안의 경로"):
        w.save_files(st, doc, "-", {"../x.md": "밖"})
