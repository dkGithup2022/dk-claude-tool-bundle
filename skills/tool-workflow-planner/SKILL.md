---
name: tool-workflow-planner
description: 워크플로 제작의 진입점. 요청으로 계획서(흐름도와 단계별 상세)를 채워 보이고, 채울 수 없으면 tool-workflow-planner-extract-plan 으로 사용자와 대화해 채운다. 확답을 받은 뒤 단계마다 tool-add-*-task 를 부르고, 반복 항목 함수·선언 파일·FLOWS 등록으로 조립하고, 끝까지 실행하는 시험으로 검증한다.
---

# tool-workflow-planner (초안)

## 0. 배경

dk-claude-tool-bundle 로 만든 프로젝트에 워크플로를 더하는 진입점이다. 워크플로는 engine 이 선언(`FlowDefinition`)을 따라 단계를 하나씩 실행하는 기능이다.
이 스킬은 계획서를 확답받고, 하위 스킬을 정해진 순서로 부르고, 결과를 조립해 등록한다.
계획서의 형식·추론 규칙·대화 순서는 `tool-workflow-planner-extract-plan`, 단계 하나의 코드는 `tool-add-*-task` 가 맡는다.

## 1. 입력과 산출물

- **입력**: 워크플로 요청. 말로 된 설명, 흐름도, 계획서 중 무엇이든.
- **사전 조건**: `tool-init` 으로 만든 프로젝트 (`src/{pkg}/engine/` 이 있음). `{pkg}` 는 `src/` 아래 유일한 폴더 이름.
- **산출물**:

```
specs/plans/workflow-<이름>.md                  계획서                       (3 절 1·2)
src/{pkg}/workflow/<이름>/
├─ __init__.py
├─ <이름>_flow.py                               선언                         (5 절)
├─ <노드 경로>/<노드 이름>_task.py ...          단계                         (tool-add-*-task)
└─ <묶음 경로>/<항목 이름>_items.py             반복 항목 함수               (5 절)
plugin/agents/<에이전트 이름>.md                 SUBAGENT 단계가 있을 때      (tool-add-subagent-task)
src/{pkg}/workflow/registry.py                  FLOWS 에 한 줄               (5 절)
tests/workflow/test_<이름>.py                   끝까지 실행하는 시험         (6 절)
```

## 2. 부르는 스킬

| 스킬 | 언제 | 넘기는 것 |
|---|---|---|
| `dk-claude-tool-bundle:tool-workflow-planner-extract-plan` | 3 절 1·2 의 조건일 때 | 계획서 경로 |
| `dk-claude-tool-bundle:tool-planner` | 단계별 상세에 "새로 필요" 한 model·port 가 있을 때 | 그 목록 |
| `dk-claude-tool-bundle:tool-add-code-task` | 종류가 `CODE` 인 단계마다 | 계획서 경로, 노드 경로 |
| `dk-claude-tool-bundle:tool-add-prompt-task` | `CLAUDE_P` 인 단계마다 | 계획서 경로, 노드 경로 |
| `dk-claude-tool-bundle:tool-add-session-task` | `MAIN_SESSION_SHOW` / `ASK` / `TALK` 인 단계마다 | 계획서 경로, 노드 경로 |
| `dk-claude-tool-bundle:tool-add-subagent-task` | `SUBAGENT` 인 단계마다 | 계획서 경로, 노드 경로 |

## 3. 작업 순서

한 단계를 끝내기 전에 다음 단계로 가지 않는다. 단계가 끝날 때마다 계획서의 상태를 바로 고친다.

1. **계획서 만들기**
   - 같은 이름의 계획서가 있으면 7 절(이어 하기)로 간다.
   - 요청이 계획서·흐름도면 그대로 옮기고, 말이면 extract-plan 3 절의 추론 규칙으로 채운다. 형식은 extract-plan 2 절. 추론한 값 뒤에는 `(추론)` 을 붙인다.
   - 아래 중 하나면 채우지 말고 `tool-workflow-planner-extract-plan` 을 부른다.
     - 요청만으로 흐름도를 그릴 수 없다: 어떤 단계가 있는지, 그 순서, 사용자에게 무엇을 보이거나 묻는지 중 하나라도 정할 수 없다.
     - 사용자가 대화로 정하자고 한다.
2. **확답**
   - 흐름도와 단계별 상세를 한 번에 보인다.
   - 사용자가 항목 몇 개를 고치면 바로 고쳐 다시 보인다. 단계를 더하거나 빼거나 순서를 바꾸자고 하면 extract-plan 을 부른다.
   - extract-plan 4 절의 확인 목록을 통과해야 확답을 받는다. 결과는 `## 확인 결과` 에 적는다.
   - 확답이면 `## 계획서 확답` 을 `확답` 으로 바꾼다.
3. **준비** (해당할 때만)
   - 단계별 상세에 "새로 필요: ..." 가 있으면 `tool-planner` 를 한 번 부른다.
   - 끝나면 만들어진 클래스·메서드 이름을 단계별 상세와 맞춘다. 상세를 고쳤으면 그 단계만 다시 확답받는다.
4. **단계 제작**
   - 흐름도 위에서 아래 순서로, 단계마다 2 절 표의 스킬 하나를 부른다.
   - 부르기 전에 노드 폴더까지의 폴더를 만들고, 폴더마다 `__init__.py` 가 없으면 빈 파일로 만든다.
   - 계획서 `## 같이 쓰는 코드` 에 그 단계가 있으면, 처음 쓰는 단계의 스킬에 "<위치>에 <무엇>을 만든다"를, 뒤 단계의 스킬에는 "<위치>의 <무엇>을 쓴다"를 같이 넘긴다.
   - 스킬이 끝나면 `## 진행 기록` 에 한 줄을 적는다: 노드 경로, 만든 파일, 검증 결과. 검증이 실패하면 다음 단계로 가지 않는다.
   - 스킬이 멈추면(계획서와 실제가 어긋남) 그 단계의 상세를 사용자와 고쳐 다시 확답받고, 그 단계부터 다시 한다.
5. **조립과 등록**: 5 절 스펙대로 반복 항목 함수 → 선언 파일 → `FLOWS` 등록 → 시작 확인.
6. **검증**: 6 절.
7. **완료 보고**: 만든 파일(단계별), 시험 결과, 써 보는 방법 `/{pkg}:run <이름>`, 계획서 경로.

## 4. 단계 제작 스킬이 기대하는 계획서

단계 제작 스킬은 계획서의 `### <노드 경로>` 절 하나만 읽고 코드를 만든다. 그 절의 상태가 `확답` 이고 extract-plan 2.3·2.4 절의 필수 항목이 모두 있어야 한다. 빠지면 스킬이 멈춘다.

## 5. 조립 스펙

### 5.1 흐름도 → 선언

| 흐름도 | 선언 |
|---|---|
| 맨 위 줄 `<워크플로 이름>` | `group("<워크플로 이름>", ChildRun.IN_ORDER, ...)` |
| `<이름> [IN_ORDER]` | `group("<이름>", ChildRun.IN_ORDER, ...)` |
| `<이름> [FOR_EACH_ITEM: <노드 이름>.<필드>]` | `group("<이름>", ChildRun.FOR_EACH_ITEM, ..., for_each_item_in=Ref("<워크플로>.<항목 이름>"))` |
| `<이름> [<수행 종류>]` | `task("<이름>", PerformedBy.<수행 종류>, Ref("<워크플로>.<이름>"))` |
| `[run_if: answer_is(<노드 이름>, "<값>")]` | `run_if=Ref("answer_is", {"node_name": "<노드 이름>", "value": "<값>"})` |
| 단계별 상세의 입력이 가리키는 노드 (`← 지금 항목` 제외) | 그 단계의 `reads=(...)` |
| 묶음의 반복 항목과 조건이 가리키는 노드 | 그 묶음의 `reads=(...)` |

- 파일 `src/{pkg}/workflow/<이름>/<이름>_flow.py`, 상수 `<이름 대문자>_FLOW = FlowDefinition(name="<이름>", description="<계획서 요청 한 줄>", root=...)`.
- 들여쓰기와 줄 순서를 흐름도와 같게 쓰고 `# fmt: skip` 을 붙인다.
- 모든 단계의 `_task.py` 와 반복 항목 함수 파일을 import 한다 (`# noqa: F401`). `answer_is` 를 쓰면 `from {pkg}.engine.builtin import answer_is  # noqa: F401`.

### 5.2 반복 항목 함수

- 파일 `<묶음 폴더>/<항목 이름>_items.py`, 함수 이름 `<항목 이름>`, 등록 키 `<워크플로>.<항목 이름>`. 항목 이름은 extract-plan 3.2 절.
- 흐름도의 `<노드 이름>.<필드>` 를 읽어 `list` 로 돌려준다. 다른 계산을 넣지 않는다.

```python
@ITEM_SOURCES.register_as("demo.fruits")
def fruits() -> ItemsSource:
    def items(context: FlowContext) -> list[str]:
        return list(context.read("collect_fruits")["items"])

    return items
```

### 5.3 등록

`src/{pkg}/workflow/registry.py` 에 선언을 import 하는 줄과 `FLOWS` 항목 `"<이름>": <이름 대문자>_FLOW` 를 더한다.

### 5.4 시작 확인

```bash
{PKG}_HOME=$(mktemp -d) plugin/bin/{pkg} --session flow-check start <이름>
```

첫 지시의 `type` 이 `failed` 면 `payload.text` 의 문제를 고친다. 시작 전 검사가 잡는 것: 등록되지 않은 키, 수행 종류와 요청 종류의 짝, `output_kind` 없음, 노드 이름 겹침, `reads` 의 노드가 없거나 작업이 아니거나 뒤에 실행됨.

### 5.5 예시

흐름도:

```
demo
├─ hello              [MAIN_SESSION_SHOW]
├─ talk               [IN_ORDER]
│  ├─ listen          [MAIN_SESSION_TALK]
│  └─ collect_fruits  [CODE]
├─ check              [IN_ORDER]
│  ├─ ask_check       [MAIN_SESSION_ASK]
│  └─ confirm_each    [FOR_EACH_ITEM: collect_fruits.items]  [run_if: answer_is(ask_check, "예")]
│     └─ confirm      [MAIN_SESSION_ASK]
└─ bye                [MAIN_SESSION_SHOW]
```

선언 (`demo_flow.py`):

```python
from {pkg}.engine.builtin import answer_is  # noqa: F401
from {pkg}.workflow.demo.bye import bye_task  # noqa: F401
from {pkg}.workflow.demo.check.ask_check import ask_check_task  # noqa: F401
from {pkg}.workflow.demo.check.confirm_each import fruits_items  # noqa: F401
from {pkg}.workflow.demo.check.confirm_each.confirm import confirm_task  # noqa: F401
from {pkg}.workflow.demo.hello import hello_task  # noqa: F401
from {pkg}.workflow.demo.talk.collect_fruits import collect_fruits_task  # noqa: F401
from {pkg}.workflow.demo.talk.listen import listen_task  # noqa: F401

DEMO_FLOW = FlowDefinition(
    name="demo",
    description="실행 틀 시험용 가짜 흐름",
    root=group("demo", ChildRun.IN_ORDER,
        task("hello", PerformedBy.MAIN_SESSION_SHOW, Ref("demo.hello")),
        group("talk", ChildRun.IN_ORDER,
            task("listen", PerformedBy.MAIN_SESSION_TALK, Ref("demo.listen")),
            task("collect_fruits", PerformedBy.CODE, Ref("demo.collect_fruits"))),
        group("check", ChildRun.IN_ORDER,
            task("ask_check", PerformedBy.MAIN_SESSION_ASK, Ref("demo.ask_check")),
            group("confirm_each", ChildRun.FOR_EACH_ITEM,
                task("confirm", PerformedBy.MAIN_SESSION_ASK, Ref("demo.confirm")),
                for_each_item_in=Ref("demo.fruits"),
                run_if=Ref("answer_is", {"node_name": "ask_check", "value": "예"}),
                reads=("collect_fruits", "ask_check"))),
        task("bye", PerformedBy.MAIN_SESSION_SHOW, Ref("demo.bye"))),
)  # fmt: skip
```

## 6. 검증 스펙

`tests/workflow/test_<이름>.py` 를 만들어 CLI 로 `start` 부터 `finished` 까지 돌린다.

| 단계 종류 | 시험에서 |
|---|---|
| `CLAUDE_P` | 가짜 claude 가 출력 데이터 클래스 모양의 JSON 을 돌려준다 (`{PKG}_CLAUDE_BIN`) |
| `MAIN_SESSION_ASK` | 계획서의 선택지에서 골라 `done --answer "<답>"` |
| `MAIN_SESSION_TALK` | `done` |
| `MAIN_SESSION_SHOW` | `next` |
| `SUBAGENT` | 에이전트를 띄우지 않고, `spawn` 지시의 메시지에 적힌 결과 폴더에 시험이 파일을 쓴 뒤 `done` |

- 결과 종류가 DATA 인 단계는 `result.json` 의 필드가, FILES 인 단계는 산출물 폴더의 파일이 계획서의 출력과 같은지 본다.
- `run_if` 가 있으면 참인 경로와 거짓인 경로를 하나씩 시험한다.
- 가짜 claude, 산출물 폴더에 쓰기는 원본의 `tests/workflow/test_count_joke.py` 를 따른다.

```python
def run(capsys, *args):
    main(["--session", "s", *args])
    return json.loads(capsys.readouterr().out)


def test_should_walk_demo_to_finished_when_user_checks_each_fruit(capsys):
    seen = [run(capsys, "start", "demo")["type"]]                  # show
    seen.append(run(capsys, "next")["type"])                       # talk
    seen.append(run(capsys, "done")["type"])                       # ask: 과일마다 확인할까요?
    seen.append(run(capsys, "done", "--answer", "예")["type"])     # ask: 사과 맞나요?
    seen.append(run(capsys, "done", "--answer", "맞음")["type"])   # ask: 배 맞나요?
    seen.append(run(capsys, "done", "--answer", "아님")["type"])   # show
    seen.append(run(capsys, "next")["type"])                       # finished
    assert seen == ["show", "talk", "ask", "ask", "ask", "show", "finished"]
```

마지막에 전체 검사: `uv run ruff check .`, `uv run lint-imports`, `uv run mypy`, `uv run pytest -q`.

## 7. 이어 하기

이 스킬을 다시 부르면 계획서를 먼저 읽고 이어 할 곳을 정한다.

| 계획서 상태 | 이어 할 곳 |
|---|---|
| 흐름도나 단계별 상세가 비었거나 `확답 전` 인 단계가 있음 | 3 절 1 (필요하면 extract-plan) |
| 모두 채워졌고 `## 계획서 확답` 이 `확답 전` | 3 절 2 |
| 확답, `## 진행 기록` 에 없는 단계가 있음 | 그 단계부터 3 절 4 |
| 모든 단계가 진행 기록에 있고 선언 파일이 없음 | 3 절 5 |
