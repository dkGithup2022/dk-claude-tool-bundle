---
name: tool-add-prompt-task
description: 워크플로 단계 중 프롬프트로 수행하는 것(CLAUDE_P)의 Task 를 만든다. 단계 폴더에 prompt_{동작이름}.md(프롬프트 본문), prompt_{동작이름}_output.py(출력 데이터 클래스), Task(PromptSpec 포함)를 둔다. tool-workflow-planner 가 확답받은 계획서의 단계별 상세를 받아 작업한다.
---

# tool-add-prompt-task (초안)

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 워크플로의 단계 하나를 만드는 스킬이다. 그중 프롬프트로 수행하는 단계(claude -p 호출)를 맡는다.
워크플로는 engine 패키지(워크플로 실행 엔진)가 실행한다. engine 은 워크플로의 선언(`FlowDefinition`)을 따라 단계를 하나씩 찾아, 그 단계의 `Task` 로 요청을 만들고(`build_request`) 수행자(코드, claude -p, 메인 세션)에게 넘긴 뒤, 결과를 받아(`build_output`) 파일에 저장한다. 앞 단계의 결과는 `FlowContext` 로 읽는다.
이 스킬은 `tool-workflow-planner` 가 사용자와 확답한 계획서에서 단계 하나를 받아 그 단계의 `Task`, 프롬프트 본문, 출력 데이터 클래스를 만든다. 모든 단계가 만들어지면 `tool-workflow-planner` 가 선언을 만들고 등록한다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/references/read-previous-results.md` (앞 단계 결과 읽기), `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md` (워크플로 규칙, 특히 4.2 프롬프트).

## 1. 이 스킬의 목적

프롬프트로 수행하는 단계(`PerformedBy.CLAUDE_P`)를 만든다. 수행자가 claude -p 를 부르고, 출력은 데이터 클래스로 받는다.

- **입력**: 계획서 경로와 노드 경로. 계획서의 그 단계 상세(입력, 출력 필드의 이름·타입·설명, 프롬프트 본문 전체, 입력 글 예시)가 `확답` 이어야 한다. 아니면 멈추고 `tool-workflow-planner` 로 돌려보낸다.
- **만드는 것**: 단계 폴더의 세 파일, 출력 데이터 클래스의 시험
- **만들지 않는 것**: 선언 파일·등록 (`tool-workflow-planner`)

`{동작이름}` 은 그 단계의 노드 이름이다.

## 2. 이 모듈의 목적과 형태

```
workflow/count_joke/make_joke/
├─ make_joke_task.py              # PromptSpec 과 Task: 입력 글을 만들어 넘기고, 출력 데이터 클래스로 결과를 만듦
├─ prompt_make_joke.md            # 프롬프트 본문
└─ prompt_make_joke_output.py     # 출력 모양: 데이터 클래스
```

- 프롬프트 본문은 `.md` 파일, 출력 모양은 데이터 클래스다. claude -p 에 넘기는 JSON 스키마는 데이터 클래스에서 만들어진다 (`claude_utils/prompt/prompt_output_converter.py`).
- 수행자는 claude -p 를 부르고 호출 기록을 노드 폴더 `calls/` 에 저장한다. 출력이 데이터 클래스 모양이 아니면 그 단계는 실패로 기록된다.
- `Task.build_output` 은 dict 가 아니라 데이터 클래스 객체를 받는다.
- 결과 종류(`output_kind`)는 DATA 와 FILES 둘 다 된다. FILES 면 출력 데이터 클래스에 `list[PromptFile]` 필드를 두고, `build_output` 이 파일 이름과 내용을 돌려준다. claude -p 는 도구 없이 돌기 때문에 파일을 직접 쓰지 못하고, engine 이 산출물 폴더에 쓴다.

## 3. 대표 트리와 파일 예시 (원본의 `count_joke/make_joke/`)

**`prompt_make_joke.md`**: 계획서의 본문 그대로

```markdown
입력으로 숫자 하나가 주어진다.
그 숫자의 발음이나 모양을 이용한 한국어 말장난을 한 문장으로 만든다.
joke 필드에 그 문장만 넣는다.
```

**`prompt_make_joke_output.py`**

```python
@dataclass(frozen=True, slots=True)
class MakeJokeOutput:
    joke: str  # 숫자를 이용한 말장난 한 문장
```

**`make_joke_task.py`**

```python
MAKE_JOKE = PromptSpec(
    name="make_joke",
    prompt_file=Path(__file__).parent / "prompt_make_joke.md",
    output_type=MakeJokeOutput,
)


@TASKS.register_as("count_joke.make_joke")
class MakeJokeTask(Task):
    request_type = PromptRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> PromptRequest:
        count = context.read("count_up")["count"]               # 선언에 reads=("count_up",)
        return PromptRequest(MAKE_JOKE, f"숫자: {count}")

    def build_output(self, context: FlowContext, result: MakeJokeOutput) -> TaskOutput:
        return TaskOutput({"joke": result.joke.strip()})
```

**결과가 파일일 때** (`claude_utils/prompt/common/prompt_file.py` 의 `PromptFile`)

```python
# prompt_write_docs_output.py
@dataclass(frozen=True, slots=True)
class WriteDocsOutput:
    files: list[PromptFile]  # 만든 문서들. 파일 하나는 name(파일 이름), content(내용 전체)


# write_docs_task.py
@TASKS.register_as("guide.write_docs")
class WriteDocsTask(Task):
    request_type = PromptRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> PromptRequest:
        return PromptRequest(WRITE_DOCS, context.read("collect_topics")["text"])

    def build_output(self, context: FlowContext, result: WriteDocsOutput) -> TaskOutput:
        return TaskOutput(files={f.name: f.content for f in result.files})
```

프롬프트 본문에는 `files` 에 무엇을 넣는지 적는다 (파일마다 이름과 내용, 몇 개를 만드는지). 파일 사이를 구분자로 나눈 글을 받지 않는다.

**입력 글이 길어질 때: 함수로 나눈다**

```python
def build_find_missing_input(candidate: dict[str, Any], dialogue: list[Utterance]) -> str:
    lines = [f"후보: {candidate['title']} ({candidate.get('when') or '시각 없음'})", "", "대화:"]
    lines += [f"{u.role}: {u.text}" for u in dialogue]
    return "\n".join(lines)
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

**프롬프트 본문**

- 계획서의 본문을 그대로 `prompt_{동작이름}.md` 에 쓴다. 다듬거나 줄이지 않는다.
- 본문이 출력 필드를 하나도 설명하지 않거나, 데이터 클래스에 없는 필드를 말하면 멈추고 알린다.

**출력 데이터 클래스**

- `@dataclass(frozen=True, slots=True)`, 클래스 이름은 노드 이름을 대문자로 이은 것 + `Output`.
- 필드는 계획서의 출력 필드 그대로. 필드마다 줄 끝 주석으로 한 줄 설명.
- 타입은 `str`, `int`, `float`, `bool`, `list[X]`, `dict[str, X]`, `X | None`, 다른 데이터 클래스만. 모든 필드가 필수이고 정의하지 않은 필드는 받지 않는다. 비어도 되면 `X | None`.
- 결과 종류가 FILES 면 파일 목록 필드의 타입은 `list[PromptFile]` 이다. 파일 모양을 새로 만들지 않는다.
- 하위 모양이 필요하면 같은 파일이 아니라 `prompt_{동작이름}_{하위 이름}.py` 에 데이터 클래스를 하나 더 둔다.

**`PromptSpec` 과 Task**

- `PromptSpec` 은 `_task.py` 안의 상수 (이름은 노드 이름을 대문자로). 모델(기본 sonnet)과 시간 제한(기본 300초)은 계획서에 따로 적혀 있을 때만 바꾼다.
- 등록 키 `<워크플로>.<노드 이름>` (노드 이름은 워크플로 안에서 겹치지 않는다), `request_type = PromptRequest`, `output_kind` 는 계획서의 결과 종류대로.
- 입력 글은 계획서의 예시 모양대로 `build_request` 에서 만든다. 앞 결과를 여럿 엮으면 `build_{동작이름}_input` 함수로 나눠 단계 폴더에 둔다.
- `build_output` 은 데이터 클래스에서 계획서의 결과로 옮긴다. DATA 면 결과 필드로 (JSON 으로 저장되므로 하위 데이터 클래스는 `dataclasses.asdict` 로 바꾼다), FILES 면 `TaskOutput(files={f.name: f.content for f in ...})`.

**금지**

- `build_output` 에서 dict 로 꺼내 쓰지 않는다 (`result["joke"]` 금지, `result.joke`).
- JSON 스키마를 손으로 쓰지 않는다.
- 상태 파일을 직접 읽거나 쓰지 않는다.

## 5. 있는 것 먼저 확인

- 그 노드 폴더에 파일이 이미 있으면 계획서와 다른 곳을 보여 주고 바꿀지 묻는다.
- 같은 등록 키가 이미 있으면 멈추고 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/workflow/<워크플로> tests/workflow
uv run mypy
uv run pytest -q tests/workflow/<워크플로>
```

출력 데이터 클래스마다 시험 하나: 스키마가 만들어지는지와, 예시 JSON 이 데이터 클래스로 바뀌는지.

```python
def test_should_turn_make_joke_output_json_into_dataclass():
    converter = PromptOutputConverter()
    assert converter.to_schema(MakeJokeOutput)["required"] == ["joke"]
    assert converter.to_data(MakeJokeOutput, {"joke": "팔팔"}) == MakeJokeOutput("팔팔")
```

진짜 claude -p 는 부르지 않는다. 단계 전체는 `tool-workflow-planner` 의 끝까지 실행하는 시험(가짜 claude)이 확인한다.

## 7. 산출물

- 만든 세 파일과 등록 키
- 계획서 `## 진행 기록` 에 한 줄: 노드 경로, 파일, 키, 검증 결과
