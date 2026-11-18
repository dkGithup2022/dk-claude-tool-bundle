"""Claude Code 대화 기록(JSONL)에서 사용자와 Claude 의 직접 대화만 뽑는다.

뺀다: 도구 호출과 결과(선택지 질문 제외), 서브에이전트 기록, 메타(스킬 본문, 다른 세션 메시지, 알림), 압축 요약,
Claude Code 가 만든 안내문(한도, API 오류).
넣는다: 사람이 입력한 말(붙여넣은 글 포함), 선택지 질문의 답, 대기 중 입력, 슬래시 명령(명령과 인자),
Claude 의 답글과 선택지 질문.
모르는 종류는 넣지 않는다.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from package.claude_utils.transcript.dto.utterance import Utterance

ASK = "AskUserQuestion"
_CMD = re.compile(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", re.S)


def records(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def dialogue(path: Path, until: str | None = None) -> list[Utterance]:
    """until 까지의 직접 대화. 시간 순. 시각은 초 단위로 비교한다 (대화 기록은 밀리초)."""
    rows: list[tuple[str, str, str]] = []  # (at, role, text)
    ask_ids: set[str] = set()
    for r in records(path):
        at = str(r.get("timestamp", ""))
        if r.get("isSidechain") or r.get("isMeta") or r.get("isCompactSummary"):
            continue
        content = (r.get("message") or {}).get("content")
        synthetic = (r.get("message") or {}).get("model") == "<synthetic>"  # Claude Code 가 만든 안내문
        if r.get("type") == "assistant" and isinstance(content, list) and not synthetic:
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and str(b.get("text", "")).strip():
                    rows.append((at, "assistant", str(b["text"])))
                elif b.get("type") == "tool_use" and b.get("name") == ASK:
                    ask_ids.add(str(b.get("id")))
                    rows.append((at, "assistant", _ask_text(b)))
        elif r.get("type") == "user":
            rows += [(at, "user", t) for t in _user_texts(r, content, ask_ids)]
        elif r.get("type") == "attachment":
            a = r.get("attachment") or {}
            kind = (a.get("origin") or {}).get("kind")
            human = kind in (None, "human") and a.get("commandMode") != "task-notification"
            if a.get("type") == "queued_command" and human and isinstance(a.get("prompt"), str):
                rows.append((at, "user", a["prompt"]))
    rows = [x for x in rows if not until or x[0][:19] <= until[:19]]
    rows.sort(key=lambda x: x[0])
    out, n = [], {"user": 0, "assistant": 0}
    for at, role, text in rows:
        n[role] += 1
        out.append(Utterance(f"{role[0]}{n[role]}", role, text, at))
    return out


def _user_texts(r: dict[str, Any], content: Any, ask_ids: set[str]) -> list[str]:
    if isinstance(content, str):
        if (r.get("origin") or {}).get("kind") not in (None, "human"):
            return []
        m = _CMD.search(content)
        if m:  # 슬래시 명령: "<명령> <인자>"
            return [f"{m.group(1)} {m.group(2)}".strip()]
        return [] if content.startswith("<") and not content.startswith("<pasted_content") else [content]
    if not isinstance(content, list):
        return []
    is_ask_result = any(
        isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in ask_ids for b in content
    )
    if not is_ask_result:
        return []
    tur = r.get("toolUseResult")
    answers = tur.get("answers") if isinstance(tur, dict) else None
    if isinstance(answers, dict):
        return [a for a in answers.values() if isinstance(a, str) and a.strip()]
    return []


def _ask_text(block: dict[str, Any]) -> str:
    """선택지 질문을 사람이 읽는 글로: 질문과 선택지."""
    out = []
    for q in (block.get("input") or {}).get("questions") or []:
        if isinstance(q, dict):
            opts = " / ".join(str(o.get("label")) for o in q.get("options") or [] if isinstance(o, dict))
            out.append(f"{q.get('question', '')}\n선택지: {opts}" if opts else str(q.get("question", "")))
    return "\n".join(out)
