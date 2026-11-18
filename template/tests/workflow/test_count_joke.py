"""count_joke 를 CLI 로 끝까지: 코드 → claude -p (가짜) → 서브에이전트(시험이 대신 씀) → 보이기."""

import json
import stat
from pathlib import Path

from package.common import files
from package.entry.cli import main
from package.port.local.counter.default_counter_reader import DefaultCounterReader


def _fake_claude(tmp_path, monkeypatch, joke: str):
    out = {"structured_output": {"joke": joke}, "total_cost_usd": 0.01, "num_turns": 1}
    exe = tmp_path / "fake-claude"
    exe.write_text(f"#!/bin/bash\ncat > /dev/null\necho '{json.dumps(out, ensure_ascii=False)}'")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PACKAGE_CLAUDE_BIN", str(exe))


def run(capsys, *args):
    main(["--session", "s", *args])
    return json.loads(capsys.readouterr().out)


def test_should_count_up_make_joke_and_show_it(tmp_path, monkeypatch, capsys, package_home):
    _fake_claude(tmp_path, monkeypatch, "팔(8)이 아파서 팔팔하지 못해요. ")
    # 첫 실행: 0 → 1
    spawn = run(capsys, "start", "count_joke")
    assert spawn["type"] == "spawn" and spawn["payload"]["agent"] == "package:joke-note-writer"
    assert "말장난: 팔(8)이 아파서 팔팔하지 못해요." in spawn["payload"]["message"]
    folder = Path(spawn["payload"]["message"].split("결과 폴더: ")[1])
    assert folder.name == "files" and folder.parent.name.startswith("write_note_")
    (folder / "note.md").write_text("# 해설")  # 서브에이전트 대신 산출물 폴더에 씀
    show = run(capsys, "done")
    assert show["type"] == "show" and show["payload"]["text"] == "팔(8)이 아파서 팔팔하지 못해요.\n\n# 해설"
    assert run(capsys, "next")["type"] == "finished"
    assert DefaultCounterReader().read().value == 1
    # 두 번째 실행: 1 → 2, 프롬프트 입력에 2 가 들어감. 메모 없이 done 하면 말장난만 보이고 경고를 남김
    run(capsys, "start", "count_joke")
    assert run(capsys, "done")["payload"]["text"] == "팔(8)이 아파서 팔팔하지 못해요."
    run(capsys, "next")
    assert DefaultCounterReader().read().value == 2
    runs = sorted((package_home / "sessions" / "s" / "runs").iterdir())
    calls = list(runs[-1].glob("make_joke_*/calls/1/request.json"))
    assert files.read_json(calls[0])["user"] == "숫자: 2"
    assert "경고: 산출물 폴더가 비어 있음" in (runs[-1] / "history.jsonl").read_text()
