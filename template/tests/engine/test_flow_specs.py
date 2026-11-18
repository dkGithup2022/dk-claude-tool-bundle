from package.claude_utils.prompt.dto.prompt_call_record import PromptCallRecord
from package.engine.definition.ref import Ref
from package.engine.instruction.instruction import Instruction
from package.engine.instruction.instruction_converter import InstructionConverter
from package.engine.instruction.instruction_type import InstructionType
from package.engine.model.history.history_entry import HistoryEntry
from package.engine.model.result.fixed_items import FixedItems
from package.engine.model.result.node_result import NodeResult
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.flow_run_status import FlowRunStatus
from package.engine.model.run_state.node_kind import NodeKind
from package.engine.model.run_state.node_status import NodeStatus
from package.engine.model.run_state.scenario_node import ScenarioNode
from package.engine.model.session.claude_session import ClaudeSession
from package.engine.performer.performed_by import PerformedBy
from package.engine.port.history.history_file_converter import HistoryFileConverter
from package.engine.port.result.fixed_items_file_converter import FixedItemsFileConverter
from package.engine.port.result.node_result_file_converter import NodeResultFileConverter
from package.engine.port.result.prompt_call_file_converter import PromptCallFileConverter
from package.engine.port.run_state.run_state_file_converter import RunStateFileConverter
from package.engine.port.session.session_file_converter import SessionFileConverter
from package.engine.request.conversation_request import ConversationRequest
from package.engine.request.question_request import QuestionRequest
from package.engine.request.show_request import ShowRequest
from package.engine.request.subagent_request import SubagentRequest
from package.engine.runner.child_run.child_run import ChildRun


def _scenario() -> ScenarioNode:
    alarm = ScenarioNode("a7c2f0e1-0000", "alarm", NodeKind.TASK, NodeStatus.WAITING, PerformedBy.MAIN_SESSION_ASK,
                         task=Ref("todo.ask_alarm"), waiting_item="2", done_items=["1"])  # fmt: skip
    enrich = Ref("answer_is", {"node_name": "c0_ask", "value": "예"})
    fill = ScenarioNode("1f9a0b2c-0000", "c4_fill", NodeKind.GROUP, NodeStatus.RUNNING,
                        child_run=ChildRun.FOR_EACH_ITEM, run_if=enrich, reads=("c0_ask",),
                        for_each_item_in=Ref("todo.candidates"), item_count=3, done_items=["1"],
                        children=[alarm])  # fmt: skip
    return ScenarioNode("c81e0000-0000", "todo", NodeKind.GROUP, NodeStatus.RUNNING, child_run=ChildRun.IN_ORDER,
                        children=[fill])  # fmt: skip


def test_should_round_trip_every_file_spec_when_saved_and_read():
    # given
    ask = Instruction(InstructionType.ASK, "a7c2f0e1-0000", "2", QuestionRequest("알람?", ("10분 전", "알람 없음")))
    objs = [
        (
            RunStateFileConverter(),
            FlowRunState("r_1", "todo", "s1", FlowRunStatus.RUNNING, "t0", "t1", _scenario(), ask),
        ),
        (
            RunStateFileConverter(),
            FlowRunState("r_1", "todo", "s1", FlowRunStatus.FINISHED, "t0", "t1", _scenario(), None),
        ),
        (
            HistoryFileConverter(),
            HistoryEntry(
                "t1",
                "a7c2f0e1-0000",
                "alarm_a7c2f0e1",
                "1",
                NodeStatus.COMPLETED,
                PerformedBy.MAIN_SESSION_ASK,
                "alarm_a7c2f0e1/result.json#1",
                ("calls/1",),
                0.01,
                3.2,
                None,
            ),
        ),  # fmt: skip
        (NodeResultFileConverter(), NodeResult({"1": {"answer": "10분 전"}, "2": {"answer": "1시간 전"}})),
        (FixedItemsFileConverter(), FixedItems(({"title": "팀 회의"}, {"title": "가족 식사"}), "t0")),
        (SessionFileConverter(), ClaudeSession("s1", "/x.jsonl", "r_1", "t0", "t1")),
    ]
    call = PromptCallRecord({"user": "u"}, {"ok": True, "cost_usd": 0.01})
    # when / then
    for converter, obj in objs:
        assert converter.to_data(converter.to_file(obj)) == obj, type(obj).__name__
    assert PromptCallFileConverter().to_data(*PromptCallFileConverter().to_file(call)) == call


def test_should_restore_payload_type_from_instruction_type():
    payloads = [
        (InstructionType.SHOW, ShowRequest("글")),
        (InstructionType.TALK, ConversationRequest("목표", "첫 말")),
        (InstructionType.SPAWN, SubagentRequest("package:writer", "메시지")),
    ]
    for kind, payload in payloads:
        ins = Instruction(kind, "u", None, payload)
        assert InstructionConverter().to_data(InstructionConverter().to_json(ins)) == ins
    assert InstructionConverter().to_json(Instruction.finished("c81e"))["payload"] == {"text": "끝났습니다."}


def test_should_name_node_folder_with_uuid_prefix():
    assert _scenario().children[0].children[0].folder_name == "alarm_a7c2f0e1"


def test_should_refuse_payload_that_does_not_match_instruction_type():
    import pytest

    from package.engine.request.code_request import CodeRequest

    for kind, payload in [(InstructionType.ASK, CodeRequest()), (InstructionType.ASK, ShowRequest("x")),
                          (InstructionType.SPAWN, ShowRequest("x"))]:  # fmt: skip
        with pytest.raises(TypeError, match="넣을 수 없는 요청"):
            InstructionConverter().to_json(Instruction(kind, "u", None, payload))
