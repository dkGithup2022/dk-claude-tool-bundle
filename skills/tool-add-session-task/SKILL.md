---
name: tool-add-session-task
description: 워크플로 단계 중 메인 세션이 수행하는 것(MAIN_SESSION_SHOW 보이기, MAIN_SESSION_ASK 묻기, MAIN_SESSION_TALK 대화)의 Task 를 만든다. tool-workflow-planner 가 확답받은 계획서의 단계별 상세를 받아 단계 폴더에 Task 파일 하나를 쓴다.
---

# tool-add-session-task (초안)

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 워크플로의 단계 하나를 만드는 스킬이다. 그중 메인 세션(사용자와 대화 중인 Claude Code 세션)이 수행하는 단계, 즉 보이기·묻기·대화를 맡는다.
워크플로는 engine 패키지(워크플로 실행 엔진)가 실행한다. engine 은 워크플로의 선언(`FlowDefinition`)을 따라 단계를 하나씩 찾아, 그 단계의 `Task` 로 요청을 만들고(`build_request`) 수행자(코드, claude -p, 메인 세션)에게 넘긴 뒤, 결과를 받아(`build_output`) 파일에 저장한다. 앞 단계의 결과는 `FlowContext` 로 읽는다.
이 스킬은 `tool-workflow-planner` 가 사용자와 확답한 계획서에서 단계 하나를 받아 그 단계의 `Task` 를 만든다. 모든 단계가 만들어지면 `tool-workflow-planner` 가 선언을 만들고 등록한다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/references/read-previous-results.md` (앞 단계 결과 읽기), `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md` (워크플로 규칙).

## 1. 이 스킬의 목적

메인 세션(사용자와 대화 중인 Claude Code 세션)이 수행하는 단계의 Task 를 만든다.

- **입력**: 계획서 경로와 노드 경로. 계획서의 그 단계 상세(종류, 입력, 출력, 상세)가 `확답` 이어야 한다. 아니면 멈추고 `tool-workflow-planner` 로 돌려보낸다.
- **만드는 것**: `src/{pkg}/workflow/<워크플로>/<노드 경로>/<노드 이름>_task.py`
- **만들지 않는 것**: 선언 파일, 등록(`tool-workflow-planner`), 다른 종류의 단계

## 2. 이 모듈의 목적과 형태

메인 세션 단계의 Task 는 메인 세션에 줄 요청을 만들고(`build_request`), 메인 세션의 답을 이 단계의 결과로 바꾼다(`build_output`).
실제로 보이고 묻고 대화하는 일은 플러그인의 `run` 스킬 글을 따르는 메인 세션이 한다. Task 는 그 내용만 정한다.

| 종류 | 요청 | 수행자가 돌려주는 값 (`result`) | 결과 기본 모양 |
|---|---|---|---|
| `MAIN_SESSION_SHOW` | `ShowRequest(text)` | 없음 (보이자마자 끝) | `{}` |
| `MAIN_SESSION_ASK` | `QuestionRequest(question, choices)` | 사용자의 답 (`str`) | `{"answer": str}` |
| `MAIN_SESSION_TALK` | `ConversationRequest(goal, opening)` | `{from, to, transcript}` | 그대로 |

## 3. 대표 트리와 파일 예시

```
workflow/demo/
├─ hello/hello_task.py                       # SHOW
├─ talk/listen/listen_task.py                # TALK
└─ check/
   ├─ choose_task.py                         # ASK 단계들이 같이 쓰는 부모 (선택지 밖의 답 거절)
   ├─ ask_check/ask_check_task.py            # ASK
   └─ confirm_each/confirm/confirm_task.py   # ASK, 지금 항목을 질문에 넣음
```

**보이기**

```python
@TASKS.register_as("demo.hello")
class HelloTask(Task):
    request_type = ShowRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ShowRequest:
        return ShowRequest("가짜 흐름을 시작합니다.")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({})
```

**묻기: 선택지 밖의 답을 받지 않음**

```python
@TASKS.register_as("demo.ask_check")
class AskCheckTask(Task):
    request_type = QuestionRequest
    output_kind = OutputKind.DATA
    choices = ("예", "아니요")

    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest("과일마다 확인할까요?", self.choices)

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        if result not in self.choices:
            raise ReplyRejectedError(f"선택지 밖의 답: {result}")   # 실행기가 같은 질문을 다시 냄
        return TaskOutput({"answer": result})
```

**묻기: 반복 안에서 지금 항목을 질문에 넣음**

```python
    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest(f"{context.current_item()} 맞나요?", self.choices)
```

**대화**

```python
@TASKS.register_as("demo.listen")
class ListenTask(Task):
    request_type = ConversationRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ConversationRequest:
        return ConversationRequest(goal="좋아하는 과일 두세 개를 듣는다", opening="좋아하는 과일이 뭐예요?")

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput(dict(result))       # {from, to, transcript}: 뒤 단계가 대화 내용을 읽을 때 씀
```

## 3.5 앞 단계의 결과 읽기

앞 단계의 결과는 `FlowContext` 로만 읽는다. 읽는 노드는 선언의 `reads` 에 노드 이름으로 적혀 있어야 한다 (`tool-workflow-planner` 가 계획서의 입력대로 적는다). 적지 않은 노드를 읽으면 실행 중에 오류가 난다.
자주 쓰는 모양은 아래와 같고, 전체 경우(반복 안의 결과 전부, 건너뛸 수 있는 단계, 대화 단계에서 오간 말)는 `${CLAUDE_PLUGIN_ROOT}/references/read-previous-results.md` 에 있다.

```python
count = context.read("count_up")["count"]                       # 결과 종류가 DATA 인 앞 단계 → dict
notes = context.read("write_note")                              # 결과 종류가 FILES 인 앞 단계 → {파일 이름: 내용}
fruit = context.current_item()                                  # 반복 안의 지금 항목
answers = [context.read("confirm", str(i))["answer"]
           for i in range(1, len(fruits) + 1)]                  # 반복 밖에서 반복 안의 결과 전부
```

## 4. 구현 규칙

- 파일 이름 `<노드 이름>_task.py`, 클래스 이름은 노드 이름을 대문자로 이은 것 + `Task` (`ask_check` → `AskCheckTask`).
- 등록 키는 `<워크플로>.<노드 이름>`. 노드 이름은 워크플로 안에서 겹치지 않는다.
- `output_kind = OutputKind.DATA`. 보이기·묻기·대화 단계의 결과는 dict 다.
- 글(보일 글, 질문, 선택지, 목표, 첫 말)은 계획서 상세에 적힌 그대로 쓴다. 바꾸거나 다듬지 않는다.
- 앞 결과를 글에 넣을 때는 계획서의 입력 그대로 `context.read("<노드 이름>")["<필드>"]` (FILES 인 앞 단계는 `{파일 이름: 내용}` 이라 내용을 그대로 보일 수 있다), 반복 안의 지금 항목은 `context.current_item()`.
- ASK 에서 "선택지 밖의 답을 받지 않음"이면 `ReplyRejectedError` 를 던진다. 받으면 그대로 결과에 넣는다.
- 같은 묶음의 ASK 단계 여럿이 같은 거절 규칙을 쓰면 부모 클래스를 그 묶음 폴더에 둔다 (`check/choose_task.py`).
- 결과 필드는 계획서의 출력과 같게 한다.
- 계획서 입력이 `run_if` 로 건너뛸 수 있는 단계를 가리키고, "결과가 없을 때 쓸 값"이 정해져 있으면 `OutputMissingError` 를 잡아 그 값을 쓴다.

**금지**

- 상태 파일(`state.json`, `history.jsonl`, 노드 폴더)을 직접 읽거나 쓰지 않는다. 앞 결과는 `FlowContext` 로만 읽는다.
- 메인 세션에게 할 일을 글로 지시하지 않는다 ("다음 명령을 부르세요" 같은 글). 그것은 `run` 스킬 글의 일이다.

## 5. 있는 것 먼저 확인

- 그 노드 폴더에 `_task.py` 가 이미 있으면, 계획서와 다른 곳을 보여 주고 바꿀지 묻는다.
- 같은 등록 키가 이미 있으면 (`grep -rn 'register_as("<키>")'`) 멈추고 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/workflow/<워크플로>
uv run mypy
```

이 단계만의 시험은 두지 않는다. `tool-workflow-planner` 의 끝까지 실행하는 시험이 확인한다.

## 7. 산출물

- 만든 파일과 등록 키
- 계획서 `## 진행 기록` 에 한 줄: 노드 경로, 파일, 키, 검증 결과
