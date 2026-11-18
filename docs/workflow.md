# workflow

## 1. workflow 란

기능 하나를 우리가 가진 engine 구성으로 실행할 수 있게 만든 것입니다. 사용자는 Claude Code 에서 `/package:run <워크플로 이름>` 으로 실행합니다.

워크플로 하나는 `workflow/<워크플로 이름>/` 폴더 하나에 들어 있고, 세 가지로 이루어집니다.

**선언(`FlowDefinition`)**: 어떤 단계를 어떤 순서로, 어떤 조건에서, 몇 번 실행할지

```python
DEMO_FLOW = FlowDefinition(
    name="demo",
    description="실행 틀 시험용 가짜 흐름",
    root=group("demo", ChildRun.IN_ORDER,                                        # 차례대로
        task("hello", PerformedBy.MAIN_SESSION_SHOW, Ref("demo.hello")),
        group("talk", ChildRun.IN_ORDER,
            task("listen", PerformedBy.MAIN_SESSION_TALK, Ref("demo.listen")),
            task("collect_fruits", PerformedBy.CODE, Ref("demo.collect_fruits"))),
        group("check", ChildRun.IN_ORDER,
            task("ask_check", PerformedBy.MAIN_SESSION_ASK, Ref("demo.ask_check")),
            group("confirm_each", ChildRun.FOR_EACH_ITEM,                         # 항목마다 반복
                task("confirm", PerformedBy.MAIN_SESSION_ASK, Ref("demo.confirm")),
                for_each_item_in=Ref("demo.fruits"),                              # 반복할 항목
                run_if=Ref("answer_is", {"node_name": "ask_check", "value": "예"}),   # 실행 조건
                reads=("collect_fruits", "ask_check"))),                          # 반복 항목 함수·조건이 읽는 앞 노드
        task("bye", PerformedBy.MAIN_SESSION_SHOW, Ref("demo.bye"))),
)
```

**`Task`**: 단계마다 실제로 하는 일. 프롬프트 호출, 코드 실행, 메인 세션의 질문·대화, 서브에이전트 (실제 코드를 줄인 모양)

```python
@TASKS.register_as("demo.ask_check")
class AskCheckTask(Task):
    request_type = QuestionRequest       # 수행자에게 넘길 요청의 종류
    output_kind = OutputKind.DATA        # 이 단계의 결과 종류: DATA(dict) 또는 FILES(텍스트 파일)

    def build_request(self, context: FlowContext) -> QuestionRequest:         # 수행자에게 넘길 요청
        return QuestionRequest("과일마다 확인할까요?", ("예", "아니요"))

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:  # 수행자의 반환값 → 이 단계의 결과
        return TaskOutput({"answer": result})
```

**조건 함수와 반복 항목 함수**: 앞 단계의 결과를 보고 실행 여부와 반복할 항목을 정함 (실제 코드를 줄인 모양)

```python
@CONDITIONS.register_as("answer_is")          # engine 기본 조건. 앞 단계의 답이 value 인가
def answer_is(node_name: str, value: str) -> RunCondition:
    return lambda context: context.read(node_name).get("answer") == value

@ITEM_SOURCES.register_as("demo.fruits")       # 반복 항목: collect_fruits 의 결과에서 과일 목록
def fruits() -> ItemsSource:
    return lambda context: list(context.read("collect_fruits")["items"])
```

전체 예시는 `workflow/demo/` 입니다.

## 2. 왜 필요한가

engine 은 실행 방식만 제공합니다. 순서대로 실행하고, 조건을 보고, 반복하고, 결과를 저장하는 일입니다.
구체적으로 어떤 작업을 할지, 그 데이터 스펙과 실행 방법, 로직, 실행되는 프롬프트를 정하는 곳이 `workflow/` 아래입니다.

워크플로는 이 문서의 제작 형식과 규칙을 지켜 만듭니다.

- 이 형식을 두는 이유는 복잡한 구현을 정해진 규칙으로 수행하기 위해서입니다. 가능하면 아래 스타일과 형식을 지킵니다.
- 단계마다 하는 일이 `Task` 하나로 나뉘어 있어서, 단계 하나만 고치거나 시험할 수 있습니다.
- 흐름도로 정의한 내용을 소스 코드로 그대로 옮기기 쉽습니다.

## 3. 거시 규칙

### 3.1 `FlowDefinition`

- 단위 트리는 engine 이 제공하는 세 가지로만 만듭니다.
  - `ChildRun.IN_ORDER`: 자식 단위를 차례대로 실행
  - `ChildRun.FOR_EACH_ITEM`: 반복 항목 함수(`for_each_item_in`)가 돌려준 항목마다 자식 단위를 실행
  - `run_if`: 조건 함수가 참일 때만 그 단위를 실행
- 앞 단위로 되돌아가기, 동시에 실행하기 같은 다른 실행 방식은 없습니다.
- 순서·조건·반복은 선언 파일(`<워크플로 이름>_flow.py`) 한 곳에만 씁니다. 선언은 `workflow/registry.py` 의 `FLOWS` 에 등록합니다.

### 3.2 폴더와 이름

- 폴더는 `FlowDefinition` 의 단위 트리와 같은 모양으로 둡니다. 폴더 이름이 곧 단위 이름(노드 이름)입니다.
- 이름에 순서 번호를 붙이지 않습니다 (`s1_`, `a_`, `c0_` 같은 접두어 금지). 하는 일로 이름을 짓습니다.
  - 까닭: 단위 이름은 다른 코드가 문자열로 참조합니다(`read("collect_fruits")`, `reads=(...)`, `answer_is` 의 `node_name`). 번호를 붙이면 단계를 끼울 때 뒤 이름과 그 참조를 모두 바꿔야 합니다.
- 워크플로 안에서 단위 이름이 겹치지 않게 합니다. 다른 묶음 안이라도 같은 이름을 쓰지 않습니다.
  - 까닭: 앞 결과를 노드 이름으로 읽습니다. 시작 전 검사가 겹치는 이름을 잡습니다.
- 클래스 하나에 파일 하나를 둡니다.
- 여러 단위가 같이 쓰는 코드는 그 단위들을 묶은 폴더에, 반복 항목 함수는 그 `FOR_EACH_ITEM` 묶음의 폴더에 둡니다.

### 3.3 `Task` 의 범위

`Task` 는 두 가지만 구현합니다. 수행자에게 넘길 요청 만들기(`build_request`)와, 수행자의 반환값으로 이 단계의 결과 만들기(`build_output`)입니다.
앞 단계의 결과를 찾아 넘겨주는 일과, 결과·상태를 파일에 저장하는 일은 실행기(`UnitRunner`)가 합니다.
그래서 `Task` 는 실행 상태 파일(`state.json`, `history.jsonl`, 노드 폴더)을 직접 읽거나 쓰지 않고, 앞 단계의 결과는 받은 `FlowContext` 로만 읽습니다.

실행기가 `Task` 를 부르는 부분 (`engine/runner/unit/default_unit_runner.py` 를 줄인 의사 코드):

```python
def next_instruction(self, state):
    node, context = self._find_next(state)              # 지금 수행할 노드와, 그 노드용 FlowContext (실행 상태, 노드, 항목 번호, 결과 읽기)
    task = TASKS.create(node.task)                       # 노드에 적힌 Ref("demo.ask_check") 로 Task 객체를 만듦
    request = task.build_request(context)                # Task: 요청 만들기. 앞 결과가 필요하면 context.read("<노드 이름>")
    done = self.performers[node.performed_by].perform(node, request, context)   # 수행자가 처리
    if done 이 메인 세션의 답을 기다려야 하는 지시:
        return self._wait(state, node, context, done)    # state.json 에 기다리는 지시를 적고, 지시를 출력
    output = task.build_output(context, result)          # Task: 수행자의 반환값 → 이 단계의 결과(TaskOutput)
    self._complete(state, node, context, output)         # 저장 (아래)

def _complete(self, state, node, context, kind, output):                  # kind: task.output_kind
    key = context.item_key or NO_ITEM_KEY                                  # 반복 밖이면 "-", 반복 안이면 "1", "2.1" …
    if kind is OutputKind.FILES:                                           # 받은 파일을 산출물 폴더에 쓰고, 폴더의 파일 전부를 결과로
        names = self.result_writer.save_files(state, node, key, output.files)
        output = TaskOutput({"files": names})                              # 비어 있으면 history 에 경고
    ref = self.result_writer.save_result(state, node, key, output)         # <노드 폴더>/result.json 에 항목 번호로 저장
    self._mark(state, node, key, NodeStatus.COMPLETED, record=False)      # 노드 상태 갱신
    self.run_state_writer.save_run(state)                                  # state.json 저장
    self._history(state, node, context.item_key, NodeStatus.COMPLETED, result_ref=ref)  # history.jsonl 한 줄
```

메인 세션의 답을 기다린 단계는 `done` 명령이 같은 순서를 이어 갑니다. 수행자가 답을 반환값으로 바꾸고(`receive_reply`), `task.build_output` 으로 결과를 만든 뒤 `_complete` 로 저장합니다.

### 3.4 결과 종류와 읽을 노드

**결과 종류.** `Task` 는 요청 종류(`request_type`)와 함께 결과 종류(`output_kind`)를 선언합니다.

| 결과 종류 | 결과 | `build_output` 이 돌려주는 것 | 뒤 단계가 읽으면 |
|---|---|---|---|
| `OutputKind.DATA` | dict. `result.json` 에 저장 | `TaskOutput({"필드": 값})` | 그 dict |
| `OutputKind.FILES` | 텍스트 파일(md, txt, 코드). 산출물 폴더에 생긴 파일 전부 | 코드·claude -p: `TaskOutput(files={"aa.md": "<내용>"})`. 서브에이전트: `TaskOutput()` (에이전트가 폴더에 직접 씀) | `{파일 이름: 내용}` |

- 결과 파일은 텍스트 파일만 둡니다. 내용을 Claude 에게 넘기거나 텍스트로 읽어 이해할 수 있게 하기 위해서입니다.
- 결과 종류는 수행자 종류와 묶이지 않습니다. 예를 들어 코드 단계도 FILES 일 수 있습니다.
- `Task` 는 파일을 직접 쓰지 않습니다. 파일 이름과 내용을 돌려주면 engine 이 산출물 폴더(`<노드 폴더>/files/`, 반복 안이면 `<노드 폴더>/<항목 번호>/files/`)에 씁니다.
- 서브에이전트에게는 `context.output_dir()` 로 받은 산출물 폴더를 메시지로 알려 줍니다. 에이전트가 파일 이름을 바꾸거나 여러 개를 만들어도 폴더에 생긴 그대로 결과가 됩니다.
- 산출물 폴더가 비어 있으면 그 단계는 빈 결과로 끝나고 `history.jsonl` 에 경고를 남깁니다. 파일이 꼭 있어야 하는 단계는 `build_output` 에서 직접 확인하고 없으면 예외를 냅니다.
- 선언한 종류와 다른 결과를 돌려주면 그 단계는 실패합니다.

**읽을 노드.** 단위가 결과를 읽는 앞 노드는 선언의 `reads` 에 노드 이름으로 적습니다.

```python
task("show_joke", PerformedBy.MAIN_SESSION_SHOW, Ref("count_joke.show_joke"), reads=("make_joke", "write_note"))
```

- 읽기는 `context.read("<노드 이름>")` 하나입니다. 읽는 쪽은 결과 종류를 확인하지 않습니다. engine 이 그 노드 `Task` 의 `output_kind` 를 보고 dict 또는 `{파일 이름: 내용}` 을 돌려줍니다.
- `reads` 에 없는 노드를 읽으면 실행 중에 오류가 납니다.
- 반복 항목 함수와 조건은 그것을 단 묶음에서 실행되므로, 그것들이 읽는 노드는 그 묶음의 `reads` 에 적습니다 (1 절의 `confirm_each`).
- 시작 전 검사는 `reads` 의 노드가 있는지, 작업(`TaskUnit`)인지, 읽는 단위보다 먼저 실행되는지 확인합니다.
- 읽는 방법의 예시는 `references/read-previous-results.md` 에 있습니다.

### 3.5 로직과 데이터의 위치

`Task` 는 연결만 합니다. 입력을 모으고(앞 단계 결과는 `FlowContext`, 저장된 데이터는 `port`), 로직을 부르고, 결과를 `TaskOutput` 으로 돌려줍니다.
로직은 그것이 다루는 데이터에 따라 둘 중 한 곳에 둡니다.

- 계속 남는 도메인 데이터를 다루는 로직: 데이터와 함께 `model/` 에 둡니다. 저장은 `port/` 를 거칩니다.
- 이 워크플로 안에서만 쓰는 계산: 그 단계 폴더에 하는 일로 이름 지은 함수 파일을 둡니다. 한두 줄이면 `_task.py` 안에 써도 됩니다.

로직을 `Task` 밖에 두면 engine 없이 로직만 시험할 수 있고, 다른 워크플로에서 다시 쓸 수 있습니다.

### 3.6 고치지 않는 것

- engine 과, 초기화 스킬이 함께 복사한 패키지(`claude_utils`, `entry`, `common` 에 처음부터 있는 파일)는 고치지 않습니다.

## 4. 제작 규칙

### 4.1 코드

**있는 것을 먼저 찾아 다시 씁니다.**

- 새 코드를 쓰기 전에 `model/`, `port/`, 다른 워크플로의 공용 코드에서 같은 데이터·기능이 있는지 찾습니다. 있으면 그것을 씁니다.
- 새 도메인 데이터가 필요하면 `model/` 에, 바깥 API·파일 접근이 필요하면 `port/` 에 README 의 규칙대로 추가합니다. 워크플로 폴더 안에 데이터 클래스나 파일 읽기·쓰기를 따로 만들지 않습니다.

**로직이 커지면 의미 단위로 함수를 나눕니다.**

- `build_request`, `build_output` 은 단계의 순서만 보여 주게 씁니다. 각 줄이 "무엇을 한다"로 읽히는 함수 호출이 되도록 나눕니다.
- 함수 하나는 한 가지 일만 합니다. 이름은 동사로 시작하고, 이름만 읽어도 무엇을 하는지 알 수 있게 짓습니다 (예: `find_overlapping_todos`, `merge_answers_into_draft`).
- 줄임말과 뜻 없는 이름(`helper`, `process`, `do_step`, `data2`)을 쓰지 않습니다.

```python
# 나눈 모양: build_output 이 순서만 보여 준다
def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
    drafts = read_drafts(context)
    existing = DefaultTodoApiReader().list_todos(*date_range_of(drafts))
    pairs = find_overlapping_pairs(drafts, existing)
    return TaskOutput({"pairs": pairs})
```

**함수를 두는 곳**

| 함수를 쓰는 범위 | 두는 곳 |
|---|---|
| 그 단계에서만 | 그 단계 폴더에, 대표 함수 이름으로 파일 하나 (예: `check_overlap/find_overlapping_pairs.py`). 한두 줄이면 `_task.py` 안 |
| 같은 묶음의 여러 단계 | 그 단계들을 묶은 폴더 |
| 여러 워크플로 | 도메인 데이터의 동작이면 `model/` 의 그 클래스 메서드 |

- `common.py`, `utils.py`, `step.py` 처럼 여러 함수를 모아 두는 이름 없는 파일을 만들지 않습니다.

### 4.2 프롬프트

LLM 호출(`CLAUDE_P`) 단계는 프롬프트 본문과 출력 모양을 파일로 따로 두고, 그 단계 폴더 안에 둡니다. `{동작이름}` 은 그 단계의 이름입니다.

```
workflow/count_joke/make_joke/
├─ make_joke_task.py               # Task 와 PromptSpec(프롬프트 파일, 출력 데이터 클래스, 모델, 시간 제한)
├─ prompt_make_joke.md             # 프롬프트 본문
└─ prompt_make_joke_output.py      # 출력 모양: 데이터 클래스
```

**`prompt_{동작이름}.md`: 프롬프트 본문**

- 무엇을 하는지, 입력이 어떤 모양인지, 지킬 규칙, 출력 필드마다 무엇을 넣는지를 적습니다.
- 출력 필드 이름은 `prompt_{동작이름}_output.py` 의 필드 이름과 같아야 합니다.

**`prompt_{동작이름}_output.py`: 출력 모양 (출력 스펙이 있을 때)**

- `@dataclass(frozen=True, slots=True)` 데이터 클래스 하나로 씁니다. 필드 이름이 claude -p 출력 JSON 의 키가 됩니다.
- 필드 타입은 JSON 으로 나타낼 수 있는 것만 씁니다: `str`, `int`, `float`, `bool`, `list[...]`, `X | None`, 다른 데이터 클래스.
- claude -p 에 넘기는 JSON 스키마는 이 클래스에서 만들어집니다 (`claude_utils/prompt/prompt_output_converter.py`). 모든 필드가 필수이고, 없는 필드는 받지 않습니다. 비어도 되는 필드는 `X | None` 으로 씁니다.
- `Task.build_output` 은 dict 가 아니라 이 데이터 클래스로 결과를 받습니다. 출력이 이 모양이 아니면 그 단계는 실패로 기록됩니다.

```python
# prompt_make_joke_output.py
@dataclass(frozen=True, slots=True)
class MakeJokeOutput:
    joke: str          # 숫자를 이용한 말장난 한 문장
```

**`PromptSpec`: 호출 설정**

- 파일을 따로 만들지 않고 `_task.py` 안에 상수로 둡니다. 프롬프트 파일, 출력 데이터 클래스, 모델(기본 sonnet), 시간 제한(기본 300초)입니다.

```python
# make_joke_task.py
MAKE_JOKE = PromptSpec(
    name="make_joke",
    prompt_file=Path(__file__).parent / "prompt_make_joke.md",
    output_type=MakeJokeOutput,
)
```

**입력 글**

- `build_request` 에서 만듭니다. 앞 단계 결과를 여러 개 엮어야 하면 `build_<동작이름>_input` 함수로 나눕니다.

## 5. 제작 요청과 작업 흐름

### 5.1 단계 종류

흐름도의 모든 줄은 아래 세 가지 값으로만 정합니다. 여기에 없는 종류(되돌아가기, 동시에 실행, 다른 모양의 조건)는 받지 않습니다.
필요하다는 요청이 오면 아래 종류로 바꿔 표현할 방법을 제안하거나, engine 을 늘리는 일로 따로 다룹니다.

**묶음의 실행 방식 (`ChildRun`)**: 자식이 있는 줄

| 값 | 뜻 |
|---|---|
| `IN_ORDER` | 자식을 위에서부터 차례대로 실행 |
| `FOR_EACH_ITEM` | 앞 결과의 목록 항목마다 자식을 실행 |

**수행 방식 (`PerformedBy`)**: 자식이 없는 줄

| 값 | 뜻 | 구현할 때 받아야 하는 것 |
|---|---|---|
| `CODE` | 소스 코드를 호출해서 수행 | 읽을 앞 결과, 하는 일, 남길 결과 필드, 재사용할 `model`·`port` |
| `CLAUDE_P` | 프롬프트로 수행 | 프롬프트 본문, 입력 글에 넣을 앞 결과, 출력 필드와 타입 (결과가 파일이면 `list[PromptFile]` 필드) |
| `MAIN_SESSION_SHOW` | 사용자에게 글을 보임 | 보일 글 |
| `MAIN_SESSION_ASK` | 사용자에게 선택지로 물음 | 질문, 선택지, 선택지 밖의 답을 받을지 |
| `MAIN_SESSION_TALK` | 사용자와 대화 | 대화 목표, 첫 말 |
| `SUBAGENT` | 서브에이전트에게 맡김 | 에이전트 지시문, 메시지에 넣을 앞 결과, 산출물 파일의 형식 |

모든 단계는 위의 것과 함께 결과 종류(`DATA` / `FILES`)와 읽을 앞 노드(`reads`)를 받습니다.

**실행 조건 (`run_if`)**: 어느 줄에나 붙일 수 있음

| 값 | 뜻 |
|---|---|
| 없음 | 항상 실행 |
| `answer_is(노드 이름, 값)` | 앞 단계의 답이 그 값일 때만 실행. 조건을 단 단위의 `reads` 에 그 노드를 적음 |

### 5.2 흐름도

이름은 노드 이름 그대로(번호 없음) 적고, 앞 결과도 노드 이름으로 가리킵니다. 한 줄이 `FlowDefinition` 의 단위 하나와 짝이 됩니다.

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

### 5.3 작업 흐름

1. **요청을 받습니다.** 말로 된 설명, 흐름도, 계획서 중 무엇이든 됩니다.
   예: "글을 보여 주고, 대화로 좋아하는 과일을 묻고, 그 결과를 확인할지 묻고, 확인한다면 하나씩 다시 묻는다."
2. **계획서를 만듭니다.** 요청으로 흐름도와 단계별 상세를 추론할 수 있으면 채워서 보입니다. 추론할 수 없으면 사용자와 대화하며 채웁니다.
3. **확답을 받습니다.** 흐름도와 단계별 상세를 한 번에 보이고 확답을 받습니다.
4. **제작합니다.** 계획서의 단계마다 맞는 제작 스킬을 부릅니다.
5. **조립하고 등록합니다.** 반복 항목 함수, 선언 파일을 만들고 `FLOWS` 에 등록한 뒤, 끝까지 실행하는 시험으로 확인합니다.

### 5.4 스킬

| 스킬 | 하는 일 |
|---|---|
| `tool-workflow-planner` | 진입점. 5.3 의 2~5 진행: 계획서 확답, 아래 제작 스킬 호출, 선언·`FLOWS` 등록, 끝까지 실행하는 시험 |
| `tool-workflow-planner-extract-plan` | 5.3 의 2 를 대화로: 흐름도와 단계별 상세를 채움. 계획서 항목의 값과 enum, 추론 규칙, 대화 순서, 케이스별 예시 |
| `tool-add-code-task` | `CODE` 단계: Task, 로직 함수, 필요한 `model`·`port` 재사용 또는 추가 |
| `tool-add-prompt-task` | `CLAUDE_P` 단계: `prompt_{동작이름}.md`, `prompt_{동작이름}_output.py`, `PromptSpec`, Task |
| `tool-add-session-task` | `MAIN_SESSION_*` 단계: 보이기·질문·대화 Task |
| `tool-add-subagent-task` | `SUBAGENT` 단계: 에이전트 정의(`plugin/agents/`), Task, 산출물 폴더를 알리는 메시지 |

- `model`·`port` 추가는 별도 스킬(`tool-planner` 와 그 아래 스킬)로 둡니다.
- `tool-planner` 는 워크플로가 아닌 일(바깥 API 연동, 유틸 기능, 모델·포트)에 씁니다. 그래서 모듈마다 권장 예시와 제작 방법(레퍼런스)이 있어야 합니다.
- 워크플로 등록은 세심해야 하므로, `tool-workflow-planner` 는 계획서를 사용자에게 확답받은 뒤에만 제작합니다.

## 6. 예시: count_joke

카운터를 1 올리고(코드 실행), 그 숫자로 말장난을 만들고(LLM 호출), 해설 메모를 쓰게 하고(서브에이전트), 사용자에게 보입니다. 원본 `workflow/count_joke/` 에 있고, 실제로 돌아갑니다.

```
count_joke (차례대로)
├─ count_up    (CODE)       카운터를 1 올린다 → {"count": 1}
├─ make_joke   (CLAUDE_P)   count_up 의 숫자로 말장난을 만든다 → {"joke": "..."}
├─ write_note  (SUBAGENT)   말장난의 해설 메모를 파일로 쓴다 → FILES {"note.md": "..."}
└─ show_joke   (SHOW)       말장난과 해설 메모를 사용자에게 보인다
```

```
model/counter/counter.py                       # Counter(value). up() 은 1 늘린 새 Counter (불변)
port/local/counter/                            # 카운터 저장: <데이터 폴더>/counter.json
├─ counter_reader.py, counter_writer.py        # 인터페이스
├─ default_counter_reader.py                   # 파일이 없으면 0
├─ default_counter_writer.py
├─ counter_file_converter.py                   # Counter ↔ JSON
└─ counter_file.py                             # 파일 위치
workflow/count_joke/
├─ count_joke_flow.py                          # COUNT_JOKE_FLOW 선언, 아래 Task 파일들을 import 해 등록
├─ count_up/count_up_task.py                   # 카운터를 읽고 up() 하고 저장
├─ make_joke/
│  ├─ make_joke_task.py                        # PromptSpec 과 Task: 숫자를 프롬프트 입력으로 넘기고, 출력에서 말장난을 꺼냄
│  ├─ prompt_make_joke.md                      # 프롬프트 본문
│  └─ prompt_make_joke_output.py               # 출력 모양: MakeJokeOutput(joke)
├─ write_note/
│  ├─ write_note_task.py                       # 앞 결과와 산출물 폴더로 메시지를 만들어 서브에이전트를 띄우게 함 (결과 종류 FILES)
│  └─ build_write_note_message.py              # 메시지 만들기
└─ show_joke/show_joke_task.py                 # 말장난과 해설 메모를 보이게 함
plugin/agents/joke-note-writer.md              # 서브에이전트 정의: 해설 메모를 메시지의 결과 폴더에 note.md 로 씀
workflow/registry.py                           # FLOWS 에 "count_joke" 등록
```

**코드 실행 (`PerformedBy.CODE`)**: 수행자는 아무것도 하지 않고, 일은 `build_output` 에서 합니다. 로직은 `model` 의 `Counter.up()`, 저장은 `port`.

```python
@TASKS.register_as("count_joke.count_up")
class CountUpTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        counter = DefaultCounterReader().read().up()
        DefaultCounterWriter().save(counter)
        return TaskOutput({"count": counter.value})          # → count_up 노드 폴더의 result.json
```

**LLM 호출 (`PerformedBy.CLAUDE_P`)**: 프롬프트 설정과 입력 글을 요청으로 넘기면, 수행자가 claude -p 를 부르고 호출 기록을 노드 폴더 `calls/` 에 저장합니다. 반환값은 출력 데이터 클래스 객체입니다.

```python
# prompt_make_joke_output.py
@dataclass(frozen=True, slots=True)
class MakeJokeOutput:
    joke: str  # 숫자를 이용한 말장난 한 문장

# make_joke_task.py
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
        count = context.read("count_up")["count"]   # 앞 단계(count_up)의 결과. 선언에 reads=("count_up",)
        return PromptRequest(MAKE_JOKE, f"숫자: {count}")

    def build_output(self, context: FlowContext, result: MakeJokeOutput) -> TaskOutput:
        return TaskOutput({"joke": result.joke.strip()})
```

```markdown
<!-- prompt_make_joke.md -->
입력으로 숫자 하나가 주어진다.
그 숫자의 발음이나 모양을 이용한 한국어 말장난을 한 문장으로 만든다.
joke 필드에 그 문장만 넣는다.
```

**서브에이전트 (`PerformedBy.SUBAGENT`)**: 메인 세션이 에이전트를 띄우고, 에이전트가 산출물 폴더에 파일을 쓴다. 메인 세션이 `done` 을 부르면 단계가 끝나고, engine 이 폴더에 생긴 파일을 결과로 모은다.

```python
AGENT = "package:joke-note-writer"  # plugin/agents/joke-note-writer.md


@TASKS.register_as("count_joke.write_note")
class WriteNoteTask(Task):
    request_type = SubagentRequest
    output_kind = OutputKind.FILES

    def build_request(self, context: FlowContext) -> SubagentRequest:
        count = context.read("count_up")["count"]
        joke = context.read("make_joke")["joke"]
        return SubagentRequest(AGENT, build_write_note_message(count, joke, context.output_dir()))  # 메시지 끝 줄: "결과 폴더: <경로>"

    def build_output(self, context: FlowContext, result: None) -> TaskOutput:
        return TaskOutput()  # 서브에이전트가 산출물 폴더에 쓴 파일은 engine 이 모은다
```

**보이기 (`PerformedBy.MAIN_SESSION_SHOW`)**

```python
@TASKS.register_as("count_joke.show_joke")
class ShowJokeTask(Task):
    request_type = ShowRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> ShowRequest:
        joke = context.read("make_joke")["joke"]
        notes = context.read("write_note")  # FILES: {"note.md": "<메모 내용>"}
        return ShowRequest("\n\n".join([joke, *notes.values()]))

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({})
```

**실행하면**: `/package:run count_joke` 의 `start` 한 번에 `count_up`(바로 끝남) → `make_joke`(claude -p 호출 후 끝남) → `write_note`(spawn 지시를 출력하고 멈춤)까지 이어서 돕니다. 메인 세션이 서브에이전트를 띄우고, 끝나면 `done` 을 부릅니다. 그러면 `show_joke` 가 지시를 내고, 메인 세션이 보인 뒤 `next` 를 부르면 `finished` 로 끝납니다.

실제로 돌린 결과:

```
counter.json                    {"value": 1}
make_joke_xxxx/result.json      {"by_item": {"-": {"joke": "숫자 1은 왜 항상 자신만만할까? 어디서나 \"일등\"이니까!"}}}
make_joke_xxxx/calls/1/         request.json(보낸 프롬프트와 입력 "숫자: 1"), response.json(ok, 비용 0.019 달러, 4.1초)
```

`make_joke` 가 `count_up` 의 숫자를 받는 방법은 선언의 `reads=("count_up",)` 과 `context.read("count_up")` 한 줄입니다. `Task` 끼리는 서로를 import 하지 않습니다. 다른 읽기 방법은 `references/read-previous-results.md` 에 있습니다.
