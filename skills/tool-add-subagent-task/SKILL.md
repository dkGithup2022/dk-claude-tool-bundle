---
name: tool-add-subagent-task
description: 워크플로 단계 중 서브에이전트가 수행하는 것(SUBAGENT)을 만든다. plugin/agents/ 에 에이전트 정의(지시문)를 두고, 단계 폴더에 Task 와 메시지를 만드는 함수를 둔다. 서브에이전트는 engine 이 정한 산출물 폴더에 파일을 쓰고, 그 폴더의 파일 전부가 단계의 결과가 된다. tool-workflow-planner 가 확답받은 계획서의 단계별 상세를 받아 작업한다.
---

# tool-add-subagent-task (초안)

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 워크플로의 단계 하나를 만드는 스킬이다. 그중 서브에이전트가 수행하는 단계(글쓰기처럼 도구를 써서 파일을 만들어 내는 일)를 맡는다.
워크플로는 engine 패키지(워크플로 실행 엔진)가 실행한다. engine 은 워크플로의 선언(`FlowDefinition`)을 따라 단계를 하나씩 찾아, 그 단계의 `Task` 로 요청을 만들고(`build_request`) 수행자에게 넘긴 뒤, 결과를 받아(`build_output`) 저장한다. 앞 단계의 결과는 `FlowContext` 로 읽는다.
서브에이전트 단계에서 engine 은 메인 세션에 "이 에이전트를 이 메시지로 띄우라"는 지시(`spawn`)를 낸다. 메인 세션은 플러그인의 `run` 스킬 글대로 Agent 도구로 띄우고, 끝나면 `done` 을 부른다. engine 은 그 단계의 산출물 폴더에 생긴 파일을 모두 모아 결과로 저장한다.
이 스킬은 `tool-workflow-planner` 가 사용자와 확답한 계획서에서 단계 하나를 받아 만든다. 모든 단계가 만들어지면 `tool-workflow-planner` 가 선언을 만들고 등록한다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md`, `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md` (3.4 결과 종류와 읽을 노드), `${CLAUDE_PLUGIN_ROOT}/references/read-previous-results.md` (앞 단계 결과 읽기).

## 1. 이 스킬의 목적

서브에이전트가 수행하는 단계(`PerformedBy.SUBAGENT`)를 만든다.

- **입력**: 계획서 경로와 노드 경로. 계획서의 그 단계 상세가 `확답` 이어야 한다. 아니면 멈추고 `tool-workflow-planner` 로 돌려보낸다.
  - 에이전트 지시문 전체 (무엇을, 어떤 방법으로, 산출물 파일의 형식과 예시)
  - 에이전트가 쓸 도구 (`Read`, `Write` 등)와 모델
  - 메시지에 넣을 앞 결과
  - 결과 종류 (보통 `FILES`)와 산출물 파일의 형식
- **만드는 것**: `plugin/agents/<에이전트 이름>.md`, 단계 폴더의 Task·메시지 함수
- **만들지 않는 것**: 선언 파일·등록 (`tool-workflow-planner`)

## 2. 이 모듈의 목적과 형태

```
plugin/agents/
└─ joke-note-writer.md                       # 에이전트 정의: 이름, 설명, 도구, 모델, 지시문
workflow/count_joke/write_note/
├─ write_note_task.py                        # Task: 앞 결과와 산출물 폴더로 메시지를 만들어 요청을 만듦
└─ build_write_note_message.py               # 메시지 만들기
```

- 서브에이전트는 메인 세션과 대화를 나누지 않는다. 메시지 하나를 받고, 산출물 폴더에 파일을 쓰고 끝난다.
- 산출물 폴더는 engine 이 정한다: 반복 밖이면 `<노드 폴더>/files/`, 반복 안이면 `<노드 폴더>/<항목 번호>/files/`. 실행 폴더 안이라 실행마다 따로 남는다. Task 는 `context.output_dir()` 로 그 경로를 받아 메시지에 넣는다.
- `done` 을 받으면 단계가 끝난다. 결과 종류가 `FILES` 면 engine 이 폴더에 생긴 파일 전부를 결과로 적는다. 에이전트가 이름을 바꾸거나 여러 개를 만들어도 생긴 그대로 결과다.
- 폴더가 비어 있으면 빈 결과로 끝나고 `history.jsonl` 에 경고가 남는다.
- 결과 파일은 텍스트 파일(md, txt, 코드)만 둔다. 뒤 단계가 내용을 그대로 읽어 프롬프트 입력이나 메시지에 넣기 때문이다.
- 에이전트 이름은 플러그인 이름을 붙여 부른다: `{pkg}:<에이전트 이름>`.

## 3. 대표 트리와 파일 예시 (원본의 `count_joke/write_note/`)

**`plugin/agents/joke-note-writer.md`**: 계획서의 지시문 그대로

```markdown
---
name: joke-note-writer
description: {pkg} 의 count_joke 워크플로가 띄운다. 숫자 말장난 하나의 해설 메모를 써서 정해진 폴더에 저장한다
tools: Write
model: haiku
maxTurns: 4
---

# 작업

숫자 말장난 하나의 해설 메모를 써서, 메시지의 "결과 폴더" 에 `note.md` 로 저장한다.

# 방법

- 메시지에 숫자, 말장난, 결과 폴더 경로가 있다.
- 메모는 마크다운. 제목(말장난 그대로), 어디가 재미있는지(숫자의 발음이나 모양을 어떻게 썼는지) 두세 문장.
- Write 로 결과 폴더에 저장한다. 결과 폴더 밖에는 쓰지 않는다.

# 끝내기 전 확인

- 결과 폴더에 메모가 저장되었는가.

# 결과 형식과 예시

(산출물 파일의 예시)
```

**`build_write_note_message.py`**: 메시지. 마지막 줄이 산출물 폴더

```python
def build_write_note_message(count: int, joke: str, output_dir: Path) -> str:
    return "\n".join([
        f"숫자: {count}",
        f"말장난: {joke}",
        f"결과 폴더: {output_dir}",
    ])
```

**`write_note_task.py`**

```python
AGENT = "{pkg}:joke-note-writer"  # plugin/agents/joke-note-writer.md


@TASKS.register_as("count_joke.write_note")
class WriteNoteTask(Task):
    request_type = SubagentRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> SubagentRequest:
        count = context.read("count_up")["count"]       # 앞 단계 결과. 선언에 reads=("count_up", "make_joke")
        joke = context.read("make_joke")["joke"]
        return SubagentRequest(AGENT, build_write_note_message(count, joke, context.output_dir()))

    def build_output(self, context: FlowContext, result: None) -> TaskOutput:
        return TaskOutput()  # 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 모은다
```

뒤 단계는 `context.read("write_note")` 로 `{"note.md": "<메모 내용>"}` 을 받는다.

**파일이 꼭 있어야 하는 단계**: engine 은 빈 폴더를 실패로 보지 않는다. 계획서에 "파일이 없으면 실패"라고 적혀 있을 때만 `build_output` 에서 확인한다.

```python
    def build_output(self, context: FlowContext, result: None) -> TaskOutput:
        if not any(context.output_dir().iterdir()):
            raise FileNotFoundError("메모가 없습니다")   # 그 단계가 실패로 기록되고, next 가 같은 지시를 다시 낸다
        return TaskOutput()
```

## 4. 구현 규칙

**에이전트 정의**

- 파일 `plugin/agents/<에이전트 이름>.md`. 이름은 영문 소문자와 `-`, 하는 일로 짓는다 (`joke-note-writer`).
- 앞머리: `name`, `description`(어느 워크플로가 띄우고 무엇을 하는지), `tools`(필요한 것만), `model`, `maxTurns`.
- 본문: `# 작업`, `# 방법`, `# 끝내기 전 확인`, `# 결과 형식과 예시`. 계획서의 지시문을 그대로 쓰고 다듬지 않는다.
- 지시문에 반드시 들어갈 것: 메시지의 "결과 폴더" 에 저장한다, 결과 폴더 밖에는 쓰지 않는다, 텍스트 파일로 쓴다.
- 파일 이름을 정해 두면(`note.md`) 뒤 단계가 다루기 쉽다. 그래도 뒤 단계는 이름이 달라지거나 파일이 여럿이어도 동작하게 만든다.
- 도구는 일에 필요한 것만 준다. 파일을 써야 하므로 `Write` 는 꼭 있다.

**메시지와 Task**

- 메시지는 `build_<동작이름>_message` 함수로 만든다. 마지막 줄은 `결과 폴더: <context.output_dir()>`.
- 메시지에 넣는 앞 결과는 계획서의 입력 그대로 읽는다 (`context.read("<노드 이름>")`, `references/read-previous-results.md`).
- 파일 이름 `<노드 이름>_task.py`, 등록 키 `<워크플로>.<노드 이름>`, `request_type = SubagentRequest`.
- `output_kind` 는 계획서의 결과 종류대로 적는다. 서브에이전트가 파일을 남기는 단계는 `OutputKind.FILES` 이고, `build_output` 은 `TaskOutput()` 을 돌려준다.
- 에이전트 이름 상수는 `{pkg}:<에이전트 이름>`.

**금지**

- 산출물 폴더를 직접 정하지 않는다 (`common.paths.home()` 아래 경로 등). 위치는 `context.output_dir()` 하나다.
- 서브에이전트에게 산출물 폴더 말고 다른 곳(상태 파일, 다른 데이터)에 쓰게 하지 않는다.
- 파일이 생긴 것만 보고 끝난 것으로 다루지 않는다. 끝은 메인 세션이 `done` 을 부를 때다 (`run` 스킬 글이 정함).

## 5. 있는 것 먼저 확인

- 같은 이름의 에이전트 파일이 있으면 계획서와 다른 곳을 보여 주고 바꿀지 묻는다.
- 같은 등록 키가 있으면 멈추고 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/workflow/<워크플로>
uv run mypy
```

메시지 함수에 시험 하나: 앞 결과와 산출물 폴더 경로가 메시지에 들어가는지.
단계 전체는 `tool-workflow-planner` 의 끝까지 실행하는 시험이 확인한다. 그 시험에서는 서브에이전트를 띄우지 않고, `spawn` 지시의 메시지에 적힌 결과 폴더에 시험이 직접 파일을 쓴 뒤 `done` 을 부른다 (원본의 `tests/workflow/test_count_joke.py`).

## 7. 산출물

- 만든 에이전트 파일과 단계 폴더의 파일, 등록 키, 에이전트 이름
- 계획서 `## 진행 기록` 에 한 줄: 노드 경로, 파일, 키, 검증 결과
