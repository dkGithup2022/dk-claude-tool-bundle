---
name: tool-add-code-task
description: 워크플로 단계 중 코드로 수행하는 것(CODE)의 Task 와 로직 함수를 만든다. 있는 model·port 를 먼저 찾아 다시 쓰고, 로직이 커지면 의미 단위로 함수를 나눠 단계 폴더에 둔다. tool-workflow-planner 가 확답받은 계획서의 단계별 상세를 받아 작업한다.
---

# tool-add-code-task (초안)

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 워크플로의 단계 하나를 만드는 스킬이다. 그중 코드로 수행하는 단계(계산, 데이터 읽고 쓰기)를 맡는다.
워크플로는 engine 패키지(워크플로 실행 엔진)가 실행한다. engine 은 워크플로의 선언(`FlowDefinition`)을 따라 단계를 하나씩 찾아, 그 단계의 `Task` 로 요청을 만들고(`build_request`) 수행자(코드, claude -p, 메인 세션)에게 넘긴 뒤, 결과를 받아(`build_output`) 파일에 저장한다. 앞 단계의 결과는 `FlowContext` 로 읽는다.
이 스킬은 `tool-workflow-planner` 가 사용자와 확답한 계획서에서 단계 하나를 받아 그 단계의 `Task` 와 로직을 만든다. 모든 단계가 만들어지면 `tool-workflow-planner` 가 선언을 만들고 등록한다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/references/read-previous-results.md` (앞 단계 결과 읽기), `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md` (워크플로 규칙, 특히 3.4 결과 종류와 읽을 노드, 3.5 로직과 데이터의 위치, 4.1 코드).

## 1. 이 스킬의 목적

코드로 수행하는 단계(`PerformedBy.CODE`)의 Task 와 그 로직을 만든다.

- **입력**: 계획서 경로와 노드 경로. 계획서의 그 단계 상세(입력, 출력, 하는 일, 재사용할 model·port, 다시 수행)가 `확답` 이어야 한다. 아니면 멈추고 `tool-workflow-planner` 로 돌려보낸다.
- **만드는 것**: `<노드 이름>_task.py`, 필요하면 로직 함수 파일, 로직 함수의 시험
- **만들지 않는 것**: model·port (`tool-planner`), 선언 파일·등록 (`tool-workflow-planner`)

## 2. 이 모듈의 목적과 형태

코드 단계는 수행자가 아무것도 하지 않고, 일은 Task 의 `build_output` 에서 한다.
Task 는 연결만 한다: 입력을 모으고(앞 결과는 `FlowContext`, 저장된 데이터는 포트), 로직을 부르고, 결과를 `TaskOutput` 으로 돌려준다.

| 로직이 다루는 것 | 로직을 두는 곳 |
|---|---|
| 계속 남는 도메인 데이터 (카운터, 일정) | `model/` 의 메서드 (없으면 `tool-planner` 로 먼저 만든다). 저장은 포트 |
| 앞 결과만으로 하는 계산 | 단계 폴더의 함수 파일. 한두 줄이면 `_task.py` 안 |

## 3. 대표 트리와 파일 예시

```
workflow/count_joke/count_up/
└─ count_up_task.py              # 저장된 데이터를 다룸: model 의 Counter.up(), 저장은 port

workflow/demo/talk/count_fruits/
├─ count_fruits_task.py          # 앞 결과만으로 계산
└─ count_items.py                # 순수 함수
```

**저장된 데이터를 다루는 단계** (`count_up_task.py`, 원본에 있음)

```python
@TASKS.register_as("count_joke.count_up")
class CountUpTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        counter = DefaultCounterReader().read().up()      # 읽기(port) → 로직(model)
        DefaultCounterWriter().save(counter)               # 쓰기(port)
        return TaskOutput({"count": counter.value})
```

**앞 결과만으로 계산하는 단계** (`count_items.py`, `count_fruits_task.py`)

```python
def count_items(items: list[str]) -> dict[str, int]:
    """같은 항목이 몇 번 나왔는지 센다. 예: ["사과", "배", "사과"] → {"사과": 2, "배": 1}"""
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


@TASKS.register_as("demo.count_fruits")
class CountFruitsTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        items = context.read("collect_fruits")["items"]        # 선언에 reads=("collect_fruits",)
        return TaskOutput({"counts": count_items(items)})
```

**결과가 파일인 단계**: 파일 이름과 내용을 돌려주면 engine 이 산출물 폴더에 쓴다

```python
@TASKS.register_as("demo.write_fruit_list")
class WriteFruitListTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        items = context.read("collect_fruits")["items"]
        return TaskOutput(files={"fruits.md": "\n".join(f"- {item}" for item in items)})
```

**로직이 커졌을 때: `build_output` 은 순서만 보인다**

```python
    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        drafts = read_drafts(context)
        existing = DefaultTodoApiReader().list_todos(*date_range_of(drafts))
        pairs = find_overlapping_pairs(drafts, existing)
        return TaskOutput({"pairs": pairs})
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

**Task**

- 파일 이름 `<노드 이름>_task.py`, 클래스 이름은 노드 이름을 대문자로 이은 것 + `Task`, 등록 키 `<워크플로>.<노드 이름>` (노드 이름은 워크플로 안에서 겹치지 않는다).
- `request_type = CodeRequest`, `build_request` 는 `CodeRequest()` 만 돌려준다.
- `output_kind` 는 계획서의 결과 종류대로 적는다. DATA 면 `TaskOutput({"필드": 값})`, FILES 면 `TaskOutput(files={"파일 이름": "내용"})` 을 돌려준다. 파일은 텍스트(md, txt, 코드)만.
- 입력은 계획서 그대로 읽는다: `context.read("<노드 이름>")["<필드>"]` (FILES 인 앞 단계는 `{파일 이름: 내용}`), 반복 안의 지금 항목은 `context.current_item()`.
  - 입력에 `(항목 전부)` 가 붙어 있으면, 그 반복 노드의 항목 번호마다 `read(노드 이름, item_key)` 로 읽어 모은다.
  - 입력이 건너뛸 수 있는 단계를 가리키고 "결과가 없을 때 쓸 값"이 정해져 있으면 `OutputMissingError` 를 잡아 그 값을 쓴다.
- DATA 의 결과 필드와 타입은 계획서의 출력과 같게 한다. 결과는 JSON 으로 저장되므로 dataclass 는 `dataclasses.asdict` 로 바꿔 넣는다. FILES 의 파일 이름은 계획서의 출력대로.

**로직**

- 있는 것을 먼저 찾는다: `specs/models.md`, `specs/ports.md`, `src/{pkg}/model/`, `src/{pkg}/port/`, 같은 워크플로의 다른 단계 폴더.
- 함수 하나는 한 가지 일. 이름은 동사로 시작하고 이름만 읽어도 무엇을 하는지 알 수 있게 (`find_overlapping_pairs`). 줄임말과 뜻 없는 이름(`helper`, `process`, `do_step`)을 쓰지 않는다.
- 함수 파일은 대표 함수 이름으로 (`count_items.py`). 같은 묶음의 여러 단계가 쓰면 그 묶음 폴더에 둔다.
- 새 model·port 가 필요해지면 멈추고 `tool-planner` 가 먼저 필요하다고 알린다.

**다시 수행**

- 포트로 쓰는 단계는 계획서의 "다시 수행" 항목대로 한다. "안전"이면 포트가 같은 값을 두 번 받아도 결과가 같은지 확인한다. 아니면 멈추고 묻는다.

**금지**

- 상태 파일을 직접 읽거나 쓰지 않는다. 결과 파일도 직접 쓰지 않고 `TaskOutput.files` 로 돌려준다.
- `common.py`, `utils.py`, `step.py` 같은 이름 없는 모음 파일을 만들지 않는다.
- 다른 워크플로 폴더의 코드를 import 하지 않는다. 여러 워크플로가 쓸 로직이면 model 로 옮기자고 알린다.

## 5. 있는 것 먼저 확인

- 그 노드 폴더에 `_task.py` 가 이미 있으면 계획서와 다른 곳을 보여 주고 바꿀지 묻는다.
- 같은 등록 키가 이미 있으면 멈추고 알린다.
- 쓰려는 model·port 의 메서드가 계획서와 다르면(이름, 돌려주는 값) 멈추고 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/workflow/<워크플로> tests/workflow
uv run lint-imports
uv run mypy
uv run pytest -q tests/workflow/<워크플로>
```

로직 함수 파일을 만들었으면 함수마다 시험 하나: `tests/workflow/<워크플로>/test_<함수 파일 이름>.py`. Task 자체는 `tool-workflow-planner` 의 끝까지 실행하는 시험이 확인한다.

## 7. 산출물

- 만든 파일, 등록 키, 쓴 model·port
- 계획서 `## 진행 기록` 에 한 줄: 노드 경로, 파일, 키, 검증 결과
