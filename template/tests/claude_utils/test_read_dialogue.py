import json
from pathlib import Path

from package.claude_utils.transcript import read_dialogue as transcript

FIX = Path(__file__).parent.parent / "fixtures" / "transcripts" / "demo_run.jsonl"


def _write(tmp_path, rows):
    p = tmp_path / "t.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return p


def test_should_keep_only_direct_dialogue_when_reading_real_session():
    # given: U2 실제 세션 기록 (Bash 호출과 결과, 스킬 본문이 섞여 있음)
    # when
    d = transcript.dialogue(FIX)
    # then
    users = [u.text for u in d if u.role == "user"]
    said = "사과랑 배를 좋아해요. 그 정도면 충분해요."
    assert users == ["/package:run demo", said, "예", "예", "맞음", "아님"]
    texts = " ".join(u.text for u in d if u.role == "assistant")
    assert "좋아하는 과일이 뭐예요?" in texts and "정리할까요?" in texts
    # 명령 출력(JSON)은 들어오지 않음
    assert "package" not in texts.replace("package:run", "")
    assert [u.id for u in d if u.role == "user"][:2] == ["u1", "u2"]


def test_should_drop_sidechain_meta_and_tool_results(tmp_path):
    rows = [
        {"type": "user", "timestamp": "1", "message": {"content": "진짜 말"}},
        {"type": "user", "timestamp": "2", "isSidechain": True, "message": {"content": "서브에이전트 말"}},
        {"type": "user", "timestamp": "3", "isMeta": True, "message": {"content": "다른 세션 메시지"}},
        {"type": "user", "timestamp": "4", "message": {"content": [{"type": "tool_result", "tool_use_id": "x"}]}},
        {"type": "assistant", "timestamp": "5", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        {"type": "user", "timestamp": "6", "origin": {"kind": "task-notification"}, "message": {"content": "알림"}},
        {"type": "system", "timestamp": "7", "content": "시스템"},
    ]
    assert [u.text for u in transcript.dialogue(_write(tmp_path, rows))] == ["진짜 말"]


def test_should_keep_command_args_when_slash_command_has_natural_language(tmp_path):
    command = "<command-name>/package:run</command-name>"
    content = command + "\n<command-args>todo 내일 3시 치과</command-args>"
    rows = [{"type": "user", "timestamp": "1", "message": {"content": content}}]
    texts = [u.text for u in transcript.dialogue(_write(tmp_path, rows))]
    assert texts == ["/package:run todo 내일 3시 치과"]


def test_should_keep_pasted_text_and_drop_notifications_when_reading(tmp_path):
    pasted = '<pasted_content id="x">회의 초대</pasted_content id="x">\n이거 일정에 넣어 줘'
    att = {"type": "queued_command", "prompt": "<task-notification>끝</task-notification>"}
    rows = [
        {"type": "user", "timestamp": "1", "origin": {"kind": "human"}, "message": {"content": pasted}},
        {"type": "attachment", "timestamp": "2", "attachment": {**att, "commandMode": "task-notification"}},
        {"type": "attachment", "timestamp": "3", "attachment": {**att, "origin": {"kind": "peer"}}},
        {"type": "attachment", "timestamp": "4", "attachment": {"type": "queued_command", "prompt": "대기 중 입력"}},
        {"type": "assistant", "timestamp": "5",
         "message": {"model": "<synthetic>", "content": [{"type": "text", "text": "limit"}]}},
    ]  # fmt: skip
    assert [u.text for u in transcript.dialogue(_write(tmp_path, rows))] == [pasted, "대기 중 입력"]


def test_should_drop_exploration_tools_but_keep_claude_narration(tmp_path):
    # 세션이 대화 중 파일을 찾아본 경우: Read·Grep 호출과 결과는 빠지고, Claude 가 쓴 설명 글은 Claude 의 말로 남는다
    rows = [
        {"type": "user", "timestamp": "1", "message": {"content": "지난주 회의록 보고 일정 잡아 줘"}},
        {"type": "assistant", "timestamp": "2", "message": {"content": [
            {"type": "text", "text": "회의록을 먼저 보겠습니다."},
            {"type": "tool_use", "id": "r1", "name": "Read", "input": {"file_path": "/x/notes.md"}},
            {"type": "tool_use", "id": "g1", "name": "Grep", "input": {"pattern": "마감"}},
        ]}},
        {"type": "user", "timestamp": "3", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "r1", "content": "회의록 내용: 금요일 마감"},
            {"type": "tool_result", "tool_use_id": "g1", "content": "notes.md:3: 마감"},
        ]}},
    ]  # fmt: skip
    got = [(u.role, u.text) for u in transcript.dialogue(_write(tmp_path, rows))]
    assert got == [("user", "지난주 회의록 보고 일정 잡아 줘"), ("assistant", "회의록을 먼저 보겠습니다.")]
