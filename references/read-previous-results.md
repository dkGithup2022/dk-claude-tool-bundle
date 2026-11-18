# 앞 단계의 결과 읽기

워크플로의 `Task`, 조건 함수, 반복 항목 함수는 앞 단계의 결과를 `FlowContext` 로만 읽는다.
실행 상태 파일(`state.json`, `history.jsonl`, 노드 폴더)을 직접 열지 않는다. 아래 예시는 원본의 demo, count_joke 로 실제 실행해 확인한 것이다.

| 읽을 것 | 방법 |
|---|---|
| 앞 단계 결과 (DATA) | `context.read("<노드 이름>")["<필드>"]` |
| 앞 단계 결과 (FILES) | `context.read("<노드 이름>")` → `{파일 이름: 내용}` |
| 반복 안의 지금 항목 | `context.current_item()` |
| 반복 안에서 같은 항목의 앞 단계 결과 | `context.read("<노드 이름>")` (항목 번호를 주지 않으면 지금 항목 번호를 씀) |
| 반복 밖에서 반복 안의 결과 전부 | 항목 수만큼 `context.read("<노드 이름>", "<항목 번호>")` |
| 건너뛸 수 있는 단계의 결과 | `OutputMissingError` 를 잡아 정한 값을 씀 |
| 대화(TALK) 단계에서 오간 말 | 그 단계 결과의 `transcript`, `from`, `to` 로 `claude_utils.transcript.read_dialogue.dialogue` |

## 0. 읽기 전에: 선언에 적는다

읽는 노드는 읽는 단위의 선언에 `reads` 로 적는다. 적지 않은 노드를 읽으면 실행 중에 오류가 난다.

```python
task("show_joke", PerformedBy.MAIN_SESSION_SHOW, Ref("count_joke.show_joke"), reads=("make_joke", "write_note"))
```

- 노드는 이름으로 가리킨다. 워크플로 안에서 노드 이름은 겹치지 않는다 (시작 전 검사가 확인).
- 시작 전 검사는 `reads` 의 노드가 있는지, 작업(TaskUnit)인지, 읽는 단위보다 먼저 실행되는지도 확인한다.
- 반복 항목 함수와 조건은 그것을 단 묶음(group)에서 실행된다. 그래서 그것들이 읽는 노드는 그 묶음의 `reads` 에 적는다.

```python
group("confirm_each", ChildRun.FOR_EACH_ITEM,
      task("confirm", PerformedBy.MAIN_SESSION_ASK, Ref("demo.confirm")),
      for_each_item_in=Ref("demo.fruits"),                                    # collect_fruits 를 읽음
      run_if=Ref("answer_is", {"node_name": "ask_check", "value": "예"}),    # ask_check 를 읽음
      reads=("collect_fruits", "ask_check"))
```

읽는 쪽은 읽을 노드의 결과 종류(`output_kind`)를 따로 확인하지 않는다. engine 이 그 노드 Task 의 선언을 보고 DATA 면 dict 를, FILES 면 `{파일 이름: 내용}` 을 돌려준다.

## 1. 앞 단계 결과 (DATA)

```python
# count_joke/make_joke: count_up 이 남긴 {"count": 8}
count = context.read("count_up")["count"]

# demo/check/confirm_each 의 반복 항목: collect_fruits 가 남긴 {"items": ["사과", "배"]}
fruits = context.read("collect_fruits")["items"]
```

결과가 없으면 `OutputMissingError`.

## 2. 앞 단계 결과 (FILES)

서브에이전트나 claude -p 가 남긴 파일은 `{파일 이름: 내용}` 으로 읽는다. 결과 파일은 텍스트 파일(md, txt, 코드)이라 내용을 그대로 프롬프트 입력이나 메시지에 넣을 수 있다.

```python
# count_joke/show_joke: write_note 의 서브에이전트가 쓴 메모 → {"note.md": "# 팔(8)이 ..."}
notes = context.read("write_note")
text = "\n\n".join(notes.values())
```

- 파일 이름은 산출물 폴더 기준 경로다 (하위 폴더에 쓴 파일은 `"sub/b.md"`).
- 파일이 하나도 없으면 빈 dict 다. 그 단계는 경고를 남기고 끝났다.
- 에이전트가 파일 이름을 바꿀 수 있으므로, 이름이 정해진 파일만 꺼내지 말고 돌려받은 것을 모두 다룬다.

## 3. 반복 안의 지금 항목

```python
# demo/check/confirm_each/confirm: 항목 번호 "2" 를 수행 중이면 "배"
fruit = context.current_item()
```

## 4. 반복 안에서 같은 항목의 앞 단계 결과

항목 번호를 주지 않으면, 읽으려는 노드가 반복 몇 겹 안에 있는지에 맞춰 지금 항목 번호의 앞부분을 쓴다.

```python
# 반복 안에서 "2" 를 수행 중일 때
context.read("confirm")       # 같은 반복 안의 노드 → 항목 "2" 의 결과
context.read("ask_check")     # 반복 밖의 노드 → "-" 의 결과
```

## 5. 반복 밖에서 반복 안의 결과 전부

반복 밖의 단계는 지금 항목이 없으므로 항목 번호를 직접 준다. 항목 번호는 `"1"` 부터.

```python
# demo/bye 에서 (reads=("collect_fruits", "confirm")): 과일마다의 확인 답 → ["맞음", "아님"]
fruits = context.read("collect_fruits")["items"]
answers = [context.read("confirm", str(i))["answer"] for i in range(1, len(fruits) + 1)]
```

## 6. 건너뛸 수 있는 단계의 결과

`run_if` 가 거짓이라 건너뛴 단계(와 그 아래)에는 결과가 없다.

```python
# demo: ask_check 에 "아니요" 라고 답하면 confirm_each 가 통째로 건너뛰어진다
try:
    answer = context.read("confirm", "1")["answer"]
except OutputMissingError:
    answer = None          # 계획서에 정한 "결과가 없을 때 쓸 값"
```

## 7. 대화 단계에서 오간 말

`MAIN_SESSION_TALK` 단계의 결과는 `{"from": 시작 시각, "to": 끝 시각, "transcript": 대화 기록 파일 경로}` 다.
대화 기록 파일에서 그 구간의 직접 대화만 뽑는다.

```python
from pathlib import Path

from package.claude_utils.transcript.read_dialogue import dialogue

talk = context.read("listen")
lines = [u for u in dialogue(Path(talk["transcript"]), until=talk["to"]) if u.at[:19] >= talk["from"][:19]]
text = "\n".join(f"{u.role}: {u.text}" for u in lines)     # u.role: "user" / "assistant"
```

`transcript` 는 세션 시작 훅이 적은 경로라, 훅이 돌지 않은 세션에서는 `None` 일 수 있다.
