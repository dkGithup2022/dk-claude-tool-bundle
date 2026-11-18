# engine

## 1. engine 이란

실제 기능은 작업 하나로 끝나지 않습니다. 순서대로 여러 일을 하고, 조건에 따라 어떤 일은 건너뛰고, 앞에서 얻은 결과를 읽고, 같은 일을 항목마다 반복합니다.

engine 은 이런 워크플로를 선언과 작업 코드로 나눠 쓰게 하고, 실행 순서와 결과 저장은 engine 이 맡는 패키지입니다.
워크플로를 만드는 쪽은 "어떤 순서로, 어떤 조건에서, 무엇을 할지"만 선언하고, "지금 무엇을 할 차례인지, 앞 결과가 어디 있는지"는 engine 이 정합니다.

이 문서는 engine 을 잘 사용하기 위한 설명입니다.

### 1.1 용어

- **`Task`**: 수행하는 일의 단위입니다. "어떤 프롬프트를 호출한다", "어떤 코드를 호출하고 결과 데이터를 보정한다"처럼 Python 코드나 프롬프트 호출 로직이 여기서 수행됩니다.
- **`TaskUnit`, `GroupUnit`**: `Task` 에 실행 조건을 붙여 관리하는 선언입니다. `TaskUnit` 은 어떤 `Task` 를 누가 수행하고 어떤 조건(`run_if`)에서 실행할지를, `GroupUnit` 은 여러 단위를 묶어 차례대로 실행할지 항목마다 반복할지를 정합니다. 이 단위들의 트리가 워크플로 하나의 선언(`FlowDefinition`)입니다.
- **`ScenarioNode`**: 지금 실행 중인 상황에 대한 정보입니다. 실행을 시작할 때 단위마다 하나씩 만들어지고, 노드의 상태(대기, 답을 기다림, 끝남, 건너뜀, 실패)와 반복의 진행(몇 번째 항목까지 끝났는지)을 담아 `state.json` 에 저장됩니다.

### 1.2 예시: demo

실행 순서를 그림으로 그리면 아래와 같습니다. 괄호 안은 수행자(`PerformedBy`)입니다.

```
demo (차례대로)
├─ hello              (SHOW)   "가짜 흐름을 시작합니다." 를 보인다
├─ talk (차례대로)
│   ├─ listen         (TALK)   좋아하는 과일을 듣는다
│   └─ collect_fruits (CODE)   과일 목록을 결과로 남긴다 → ["사과", "배"]
├─ check (차례대로)
│   ├─ ask_check      (ASK)    "과일마다 확인할까요?" (예 / 아니요)
│   └─ confirm_each   (항목마다) ask_check 의 답이 "예"일 때만. 항목은 collect_fruits 의 결과
│       └─ confirm    (ASK)    "사과 맞나요?", "배 맞나요?"
└─ bye                (SHOW)   "가짜 흐름이 끝났습니다." 를 보인다
```

같은 내용을 `FlowDefinition` 으로 선언하면 아래와 같습니다 (`workflow/demo/demo_flow.py`).

```python
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
)
```

`Ref("demo.collect_fruits")` 가 가리키는 `Task` 는 이렇게 씁니다 (`workflow/demo/talk/collect_fruits/collect_fruits_task.py`).

```python
@TASKS.register_as("demo.collect_fruits")
class CollectFruitsTask(Task):
    request_type = CodeRequest
    output_kind = OutputKind.DATA

    def build_request(self, context: FlowContext) -> CodeRequest:
        return CodeRequest()

    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        return TaskOutput({"items": ["사과", "배"]})
```

### 1.3 실행 순서

1. `start demo`: `DEMO_FLOW` 를 본떠 `ScenarioNode` 트리를 만들고 `state.json` 에 저장합니다.
2. 명령(`next`, `done`)마다 아직 끝나지 않은 첫 노드를 찾아, 그 노드의 `Task` 를 수행자에게 넘겨 수행합니다. 조건(`run_if`)이 거짓인 노드는 건너뛰고, 반복(`FOR_EACH_ITEM`) 노드는 항목마다 자식을 수행합니다.
3. 노드마다 결과를 저장하고, 뒤 노드는 저장된 결과를 노드 이름으로 읽습니다. 읽을 노드는 선언의 `reads` 에 적습니다.

이하에서는 다음을 설명합니다.

- 2절: `FlowDefinition` 과 `Task` 의 구조
- 3절: 실행기 (`FlowRunner`, `UnitRunner`)
- 4절: 상태 파일의 저장 구조와 인터페이스
- 5절: 트리 구조
- 6절: 주의 사항

## 2. `FlowDefinition` 과 `Task` 의 구조

### 2.1 단위의 필드

| 단위 | 필드 |
|---|---|
| `TaskUnit` (`task()`) | `name` 이름, `performed_by` 수행자, `task` 실행할 `Task` 의 키, `run_if` 실행 조건 (선택), `reads` 결과를 읽는 앞 노드의 이름 (선택) |
| `GroupUnit` (`group()`) | `name` 이름, `child_run` 자식을 돌리는 방식 (`IN_ORDER` 차례대로 / `FOR_EACH_ITEM` 항목마다), `children` 자식 단위들, `for_each_item_in` 반복할 항목을 돌려주는 함수의 키 (`FOR_EACH_ITEM` 일 때), `run_if` 실행 조건 (선택), `reads` 반복 항목 함수·조건이 결과를 읽는 앞 노드의 이름 (선택) |

`Task`, 조건 함수, 반복 항목 함수는 레지스트리에 키로 등록합니다. 레지스트리는 키로 코드를 찾는 목록이고, `TASKS`, `CONDITIONS`, `ITEM_SOURCES` 세 개가 있습니다.
단위에서는 `Ref(키, args)` 로 가리킵니다. `args` 는 그 함수에 넘길 값입니다.
예를 들어 `Ref("answer_is", {"node_name": "ask_check", "value": "예"})` 는 조건 함수 `answer_is(node_name="ask_check", value="예")` 를 뜻합니다.

규칙

- 단위를 만들 때 생성자가 바로 검사합니다. 예를 들어 `FOR_EACH_ITEM` 인데 `for_each_item_in` 이 없으면 만들 때 실패합니다.
- 실행을 시작하기 전에 한 번 더 검사합니다. 키가 레지스트리에 있는지, 수행자가 받는 요청 종류와 `Task` 가 만드는 요청 종류가 같은지, `Task` 에 결과 종류(`output_kind`)가 있는지 봅니다.
- 앞 결과를 노드 이름으로 읽으므로 워크플로 안에서 노드 이름이 겹치면 안 되고, 같은 `Task` 키를 두 번 쓰면 안 됩니다. `reads` 의 노드는 있어야 하고, 작업(`TaskUnit`)이어야 하고, 읽는 단위보다 먼저 실행되어야 합니다. 시작 전 검사가 모두 확인합니다.

### 2.2 `Task` 와 수행자

`Task` 는 무엇을 할지만 정합니다. 노드 상태와 저장은 만지지 않습니다.

```python
class Task(ABC):
    request_type: ClassVar[type[TaskRequest]]              # 이 Task 가 만드는 요청 종류
    output_kind: ClassVar[OutputKind]                      # 이 Task 의 결과 종류: DATA(dict) 또는 FILES(텍스트 파일)
    def build_request(self, context) -> TaskRequest          # 수행자에게 넘길 요청
    def build_output(self, context, result) -> TaskOutput    # 수행자의 반환값(result) → 이 노드의 결과(TaskOutput)
```

수행자(`PerformedBy`)는 요청을 받아 실제로 처리하는 쪽입니다. 수행자마다 받는 요청 종류가 하나로 정해져 있습니다.
메인 세션은 사용자와 대화 중인 Claude Code 세션입니다.

| 수행자 | 받는 요청 | 하는 일 | 반환값 |
|---|---|---|---|
| `CODE` | `CodeRequest` | 없음. 일은 `build_output` 에서 코드로 함 | 없음 |
| `CLAUDE_P` | `PromptRequest` | claude -p 호출. 호출 기록을 노드 폴더에 저장 | 출력 데이터 클래스 객체 |
| `MAIN_SESSION_SHOW` | `ShowRequest` | 메인 세션이 글을 보임. 답을 기다리지 않음 | 없음 |
| `MAIN_SESSION_ASK` | `QuestionRequest` | 메인 세션이 선택지로 물음 | 사용자의 답 |
| `MAIN_SESSION_TALK` | `ConversationRequest` | 메인 세션이 사용자와 대화 | 대화를 시작하고 끝낸 시각, 대화 기록 파일 경로 |
| `SUBAGENT` | `SubagentRequest` | 메인 세션이 서브에이전트를 띄움. 서브에이전트는 산출물 폴더에 파일을 씀 | 없음 (산출물 폴더의 파일은 engine 이 모음) |

### 2.3 워크플로를 만들 때 구현할 것

| 구현할 것 | 등록하는 곳 |
|---|---|
| `Task` 를 상속한 클래스 | `@TASKS.register_as("키")` |
| 조건 함수: `FlowContext` 를 받아 `bool` 을 돌려줌 | `@CONDITIONS.register_as("키")` |
| 반복 항목 함수: `FlowContext` 를 받아 항목 `list` 를 돌려줌 | `@ITEM_SOURCES.register_as("키")` |
| `FlowDefinition` (`task()`, `group()` 으로 단위를 만듦) | `workflow/registry.py` 의 `FLOWS` |

앞 노드의 결과는 `FlowContext.read()`, `current_item()` 으로 읽습니다 (4.2 절).
폴더 모양과 선언 규칙은 `docs/workflow.md` 에 둡니다.

## 3. 실행기

### 3.1 명령 하나가 하는 일

Claude 세션은 CLI 명령(`start`, `next`, `done`)을 부를 때마다 지금 할 일 하나를 받습니다. 이 할 일을 지시(`Instruction`)라고 하며, 보이기·묻기·대화·서브에이전트 띄우기·끝·실패 중 하나입니다.
CLI 는 명령마다 새로 실행되는 프로세스입니다. 그래서 명령마다 파일에서 상태를 읽고, 한 걸음 진행하고, 다시 파일에 씁니다.

명령 하나를 처리하려면 실행기는 아래를 차례로 알아내야 합니다.

| 알아야 하는 것 | 어디서 알아내나 | 맡는 쪽 |
|---|---|---|
| 지금 진행 중인 실행은 무엇인가 | `session.json` 의 실행 id | `FlowRunner` |
| 어디까지 했나 | `state.json` 의 노드 상태, 답을 기다리는 지시 | `FlowRunner` 가 읽어 `UnitRunner` 에 넘김 |
| 지금 수행할 노드는 무엇인가 | 노드 트리를 위에서부터 훑어 끝나지 않은 첫 노드. `run_if` 가 거짓이면 건너뛰고, 반복이면 아직 안 끝난 항목 | `UnitRunner` (`_walk`) |
| 그 노드가 쓸 앞 결과는 어디 있나 | 앞 노드의 노드 폴더 (`FlowContext` 로 읽음, 4.2 절) | `Task` |
| 누가 수행하나 | 노드에 적힌 수행자 (`performed_by`) | `UnitRunner` 가 수행자에게 넘김 |
| 무엇을 남기나 | 노드의 결과는 노드 폴더에, 노드 상태는 `state.json` 에, 한 줄은 `history.jsonl` 에 | `UnitRunner` |

정리하면 `FlowRunner` 는 명령 단위로 일합니다. 어느 실행인지 찾고, 상태 파일을 읽고 쓰고, 실행을 시작하고 끝냅니다.
`UnitRunner` 는 노드 단위로 일합니다. 수행할 노드를 찾고, 수행자에게 넘기고, 결과를 남깁니다.

### 3.2 `start`: 실행 전에 노드 트리를 만드는 이유

`start` 는 `FlowDefinition` 을 본떠 `ScenarioNode` 트리를 만들고 `state.json` 에 저장합니다. 이렇게 하는 이유는 세 가지입니다.

- 노드마다 상태와 반복의 진행을 적을 자리가 필요합니다. `FlowDefinition` 은 선언이라 실행 중의 상황을 담지 않습니다.
- 노드마다 uuid 를 붙여 노드 폴더 이름(`<노드 이름>_<uuid 앞 8자>`)을 정합니다. 결과를 찾는 위치가 실행 내내 같습니다.
- 이후 명령은 `state.json` 만 보고 진행합니다. 실행 도중에 선언 코드가 바뀌어도, 진행 중인 실행의 순서·조건·반복 구성은 바뀌지 않습니다.

만들기 전에 선언을 한 번 검사합니다(`runner/scenario/check_definition.py`). 키가 레지스트리에 있는지, 수행자가 받는 요청 종류와 `Task` 가 만드는 요청 종류가 같은지 봅니다. 문제가 있으면 실행을 만들지 않습니다.

### 3.3 `next` / `done`: 노드를 수행하고 남기기

**`next`**: 답을 기다리는 지시가 있으면 그 지시를 다시 돌려줍니다. 없으면 수행할 노드를 찾아 수행합니다.

- 코드, claude -p 처럼 바로 끝나는 수행은 결과를 남기고 다음 노드로 계속 갑니다.
- 메인 세션이 해야 하는 수행(묻기, 대화, 서브에이전트)을 만나면, 노드 상태를 답을 기다림(`WAITING`)으로 바꾸고 그 지시를 출력하고 멈춥니다.
- 보이기는 결과를 남긴 뒤 지시를 출력하고 멈춥니다. 메인 세션이 글을 보인 뒤 `next` 를 부릅니다.
- 더 수행할 노드가 없으면 실행을 끝남으로 바꾸고 `finished` 를 출력합니다.

**`done`**: 기다리던 노드에 메인 세션의 답을 넣습니다. 수행자가 답을 반환값으로 바꾸고(`receive_reply`), `Task.build_output` 이 노드의 결과를 만들어 남긴 뒤, `next` 와 같이 다음 노드로 갑니다.
`Task` 가 답을 받지 않으면(`ReplyRejectedError`, 예: 선택지 밖의 답) 같은 지시를 다시 출력합니다.

**실패**: 수행 중 예외가 나면 노드 상태를 실패로 바꾸고 `failed` 를 출력합니다. 다음 `next` 가 그 노드부터 다시 수행합니다.

### 3.4 예시: demo 를 끝까지

| 명령 | 출력된 지시 | 일어난 일 |
|---|---|---|
| `start demo` | show "가짜 흐름을 시작합니다." | `ScenarioNode` 트리 저장. `hello` 수행, `COMPLETED` |
| `next` | talk "좋아하는 과일이 뭐예요?" | `listen` 이 `WAITING` |
| `done` | ask "과일마다 확인할까요?" | `listen` `COMPLETED`. `collect_fruits` 를 수행해 `["사과", "배"]` 저장. `ask_check` 가 `WAITING` |
| `done --answer 예` | ask "사과 맞나요?" (항목 번호 1) | `ask_check` `COMPLETED`. `confirm_each` 의 `run_if` 가 참. 반복 항목을 `items.json` 에 저장하고 `confirm` 항목 1 이 `WAITING` |
| `done --answer 맞음` | ask "배 맞나요?" (항목 번호 2) | `confirm` 항목 1 의 결과 저장 |
| `done --answer 아님` | show "가짜 흐름이 끝났습니다." | `confirm` 항목 2 의 결과 저장, 반복 끝. `bye` 수행 |
| `next` | finished | 실행 상태(`FlowRunStatus`)를 `FINISHED` 로 바꾸고 `session.json` 의 실행 id 를 비움 |

## 4. 상태 파일의 저장 구조와 인터페이스

워크플로는 CLI 를 여러 번 불러 진행되고, 그때마다 Python 코드나 프롬프트를 따로따로 호출합니다.
CLI 는 명령마다 새 프로세스로 뜨기 때문에 메모리에 아무것도 남지 않습니다. 그래서 지금 상태와 이전 결과를 저장해 둘 구조가 필요합니다.

engine 은 아래 파일 구조로 이 문제를 풉니다. 실행 중인 노드 트리의 각 노드가 `Task` 를 수행하기 전후로 상태를 갱신하고, 결과는 그 노드의 폴더 아래에 저장합니다.

### 4.1 저장 구조

파일은 CLI 를 부른 작업 폴더의 `.package/` 아래에 생깁니다 (환경 변수 `PACKAGE_HOME` 이 있으면 그 폴더).
처음 쓸 때 폴더가 만들어집니다. 위치 계산은 `common/paths.py` 와 `engine/port/run_location.py` 가 맡습니다.

```
.package/sessions/<Claude Code 세션 id>/
├─ session.json
└─ runs/<실행 id>/
   ├─ state.json
   ├─ history.jsonl
   ├─ <노드 이름>_<uuid 앞 8자>/
   │  ├─ result.json
   │  ├─ files/                    (결과 종류가 FILES 인 노드, 반복 안이면 <항목 번호>/files/)
   │  ├─ items.json
   │  └─ calls/<n>/request.json, response.json
   └─ ...
```

| 경로 | 무엇을 담나 | 왜 이렇게 나눴나 |
|---|---|---|
| `sessions/<Claude Code 세션 id>/` | 그 Claude Code 세션에서 돌린 실행들 | CLI 는 어느 대화에서 불렸는지 세션 id 로만 압니다(환경 변수 `CLAUDE_CODE_SESSION_ID`). 같은 작업 폴더에서 여러 세션이 각자 실행해도 섞이지 않습니다 |
| `session.json` | 지금 진행 중인 실행의 id, 대화 기록 파일 경로 | `next`, `done` 은 워크플로 이름 없이 불립니다. 이어서 할 실행을 여기서 찾습니다. 대화 기록 경로는 세션 시작 훅이 적고, 대화(TALK) 노드가 대화 내용을 읽을 때 씁니다 |
| `runs/<실행 id>/` | 실행 하나(`start` 한 번)의 모든 파일 | 한 세션에서 워크플로를 여러 번 돌릴 수 있습니다. id 는 `r_<UTC 시작 시각>` 이라 이름순이 시간순입니다 |
| `state.json` | 노드 트리, 노드마다의 상태와 반복 진행, 답을 기다리는 지시, 실행 상태 | 명령마다 이 파일 하나만 읽으면 "어디까지 했고 지금 무엇을 기다리는지"를 압니다 |
| `history.jsonl` | 노드가 기다리거나, 끝나거나, 건너뛰거나, 실패할 때마다 한 줄. claude -p 비용과 시간, 실패 내용 | `state.json` 은 지금 상태만 담습니다. 무슨 일이 어떤 순서로 있었는지는 덧붙이기만 하는 이 파일에 남깁니다 |
| `<노드 이름>_<uuid 앞 8자>/` | 노드 하나의 결과물 | 이름은 사람이 알아보라고, uuid 는 다른 묶음 안의 같은 이름 노드와 겹치지 않게 붙입니다 |
| `result.json` | 노드의 결과(`TaskOutput`). 항목 번호를 키로. 결과 종류가 FILES 인 노드는 파일 이름 목록 `{"files": [...]}` | 반복 안의 노드는 항목마다 한 번씩 수행되므로, 결과를 항목 번호별로 나눠 둡니다 |
| `files/` | 결과 종류가 FILES 인 노드의 산출물 폴더. 폴더에 있는 파일 전부가 그 노드의 결과 | 서브에이전트가 이름을 바꾸거나 여러 개를 만들어도 생긴 그대로 결과로 받기 위해서입니다. 실행 폴더 안이라 실행마다 따로 남습니다 |
| `items.json` | 반복(`FOR_EACH_ITEM`) 노드의 항목 | 처음 계산한 항목을 저장해 두고 그 뒤로는 이것을 씁니다. 반복 도중에 앞 결과가 바뀌어도 항목은 바뀌지 않습니다 |
| `calls/<n>/` | claude -p 호출 하나의 요청과 응답 | 무엇을 보냈고 무엇을 받았는지, 비용과 시간을 나중에 확인하기 위해서입니다 |

항목 번호(`item_key`)는 반복 안에서 몇 번째 항목인지를 나타냅니다.

| 노드 위치 | 항목 번호 |
|---|---|
| 반복 밖 | `"-"` (`NO_ITEM_KEY`) |
| 반복 안 | `"1"`, `"2"` |
| 반복 안의 반복 | `"2.1"` (바깥 2번째 항목 안의 1번째 항목) |

**언제 쓰나**

| 때 | 쓰는 파일 |
|---|---|
| `start` | `state.json` 을 만들고, `session.json` 에 실행 id 를 적음 |
| 노드가 메인 세션의 답을 기다릴 때 (메인 세션이 수행하기 전) | `state.json` 의 노드 상태와 기다리는 지시, `history.jsonl` 한 줄 |
| 노드가 끝났을 때 (수행한 뒤) | 노드 폴더의 `result.json`(FILES 면 받은 파일을 `files/` 에 먼저 씀), `state.json` 의 노드 상태, `history.jsonl` 한 줄. `files/` 가 비어 있으면 그 줄에 경고 |
| 반복 노드를 처음 수행할 때 | 노드 폴더의 `items.json` |
| claude -p 를 호출했을 때 | 노드 폴더의 `calls/<n>/` |
| 실행이 끝났을 때 | `state.json` 의 실행 상태, `session.json` 의 실행 id 비움 |

demo 를 돌린 뒤의 실제 내용:

```
collect_fruits_24a532dc/result.json    {"by_item": {"-": {"items": ["사과", "배"]}}}
ask_check_b31a5f27/result.json         {"by_item": {"-": {"answer": "예"}}}
confirm_each_ce1cd48c/items.json       {"items": ["사과", "배"], "fixed_at": "..."}
confirm_3e46b437/result.json           {"by_item": {"1": {"answer": "맞음"}, "2": {"answer": "아님"}}}
```

### 4.2 앞 노드의 결과 읽기

`Task`, 조건 함수, 반복 항목 함수는 모두 `FlowContext` 로만 앞 노드의 결과를 읽습니다 (`definition/context/flow_context.py`).

```python
# 반복 항목 함수: collect_fruits 의 결과에서 과일 목록 (check/confirm_each/fruits_items.py)
@ITEM_SOURCES.register_as("demo.fruits")
def fruits() -> ItemsSource:
    def items(context: FlowContext) -> list[str]:
        return list(context.read("collect_fruits")["items"])  # confirm_each 의 reads 에 collect_fruits

    return items

# Task: 지금 항목의 내용 "사과", "배" (check/confirm_each/confirm/confirm_task.py)
@TASKS.register_as("demo.confirm")
class ConfirmTask(ChooseTask):
    def build_request(self, context: FlowContext) -> QuestionRequest:
        return QuestionRequest(f"{context.current_item()} 맞나요?", self.choices)
```

- `read("노드 이름")`: 그 노드의 결과를 돌려줍니다. 읽는 단위의 `reads` 에 적힌 노드만 읽을 수 있습니다.
  - 그 노드의 결과 종류가 DATA 면 `result.json` 의 dict, FILES 면 `{파일 이름: 내용}` 입니다. 읽는 쪽은 종류를 확인하지 않습니다.
  - 항목 번호를 주지 않으면 지금 항목 번호에서 알맞은 부분을 씁니다. 예를 들어 지금 `"2.1"` 을 수행 중이면, 반복 밖 노드는 `"-"`, 바깥 반복 안의 노드는 `"2"`, 같은 반복 안의 노드는 `"2.1"` 로 읽습니다.
  - 노드를 이름으로 찾는 일은 `NodeLocator` 가 합니다 (`definition/context/node_locator.py`).
- `output_dir()`: 이 단계의 산출물 폴더. 서브에이전트 단계가 메시지에 넣어 "이 폴더에 쓰라"고 알릴 때 씁니다.
- `current_item()`: 지금 항목 번호에 해당하는 항목의 내용을 돌려줍니다 (`definition/context/find_item.py`). 가장 바깥 반복은 `items.json` 에서, 안쪽 반복은 반복 항목 함수를 다시 불러서 찾습니다.

### 4.3 인터페이스

저장 대상마다 `engine/port/` 아래 폴더 하나에 읽기 인터페이스, 쓰기 인터페이스, 기본 구현, 파일 변환기를 둡니다.
파일 변환기는 데이터 클래스와 파일에 저장하는 JSON 사이를 바꿉니다 (`to_file` / `to_data`).

| 저장 대상 | 읽기 | 쓰기 | 파일 변환기 |
|---|---|---|---|
| 세션 (`session.json`) | `SessionReader.load_session` | `SessionWriter.save_session` | `SessionFileConverter` |
| 실행 상태 (`state.json`) | `RunStateReader.load_run` | `RunStateWriter.save_run` | `RunStateFileConverter` |
| 실행 기록 (`history.jsonl`) | `HistoryReader.read_history` | `HistoryWriter.append_history` | `HistoryFileConverter` |
| 노드 폴더 (`result.json`, `files/`, `items.json`, `calls/`) | `ResultReader.read_result`, `read_files` | `ResultWriter.save_result`, `output_dir`, `save_files`, `fix_items`, `save_prompt_call` | `NodeResultFileConverter`, `FixedItemsFileConverter`, `PromptCallFileConverter` |

기본 구현의 이름은 `Default` 로 시작합니다 (예: `DefaultResultWriter`). 폴더 위치는 `engine/port/run_location.py` 가 정합니다.

## 5. 트리 구조

```
engine/
├─ model/          저장하는 데이터 클래스: session/, run_state/, history/, result/
├─ port/           저장 인터페이스와 구현 (4.3 절)
├─ definition/     선언에 쓰는 것: task/ (Task), unit/ (TaskUnit, GroupUnit, task(), group()),
│                  context/ (FlowContext), flow_definition, ref, run_condition, items_source
├─ request/        Task 가 만들어 수행자에게 넘기는 요청 6종
├─ instruction/    메인 세션에 출력하는 지시와 그 변환기 (to_json / to_data)
├─ registry/       TASKS, CONDITIONS, ITEM_SOURCES
├─ runner/         flow/ (FlowRunner: CLI 명령을 받음), unit/ (UnitRunner: 노드를 찾아 수행하고 저장),
│                  child_run/ (IN_ORDER, FOR_EACH_ITEM), scenario/ (시작 전 검사, ScenarioNode 트리 만들기)
├─ performer/      수행자: code/, claude_prompt/, main_session/ (SHOW, ASK, TALK), subagent/
├─ hook/           Claude Code 훅: 세션 시작, 멈춤
└─ builtin/        기본 조건 함수 answer_is
```

engine 밖: claude -p 실행은 `claude_utils/prompt/`, 대화 기록 읽기는 `claude_utils/transcript/`, 파일 쓰기·데이터 폴더 위치·시각은 `common/` 에 있습니다.

### 5.1 초기화 직후의 프로젝트 전체 (`template/`)

engine 을 실행하는 데 필요한 파일 전부입니다. `#` 뒤에 그 파일이 언제, 무엇을 위해 쓰이는지 적었습니다.

```
template/
├─ pyproject.toml                  # 의존성과 검사 설정. import 검사 계약 4개가 패키지 사이 의존 방향을 지키게 함
├─ plugin/                         # Claude Code 에 설치하는 플러그인
│  ├─ .claude-plugin/plugin.json   # 플러그인 이름. /package:run 처럼 명령 앞에 붙는 이름이 됨
│  ├─ bin/package                  # Claude 가 Bash 로 부르는 CLI. 레포의 uv 환경에서 python -m package 를 실행
│  ├─ hooks/hooks.json             # Claude Code 세션이 열릴 때와 멈추려 할 때 CLI 의 hook 명령을 부르도록 등록
│  ├─ skills/run/SKILL.md          # 사용자가 /package:run demo 를 치면 읽히는 글. 지시 종류마다 메인 세션이 할 일과 다음에 부를 명령을 적음
│  └─ agents/                      # SUBAGENT 수행자가 띄울 서브에이전트 정의. 예시로 count_joke 의 joke-note-writer.md
├─ scripts/trace_calls.py          # 코드 따라가기용. CLI 명령 하나를 실행하며 불린 함수를 호출 순서와 깊이대로 출력
├─ src/package/
│  ├─ __main__.py                  # python -m package 로 실행될 때의 시작점. entry/cli.py 로 넘김
│  ├─ entry/
│  │  └─ cli.py                    # 모든 명령이 처음 들어오는 곳. 명령을 해석하고, 저장 구현을 골라 실행기를 조립하고, 결과 지시를 JSON 한 줄로 출력
│  ├─ engine/
│  │  ├─ definition/                       # 워크플로를 선언할 때 쓰는 클래스
│  │  │  ├─ flow_definition.py             # 워크플로 하나의 선언. workflow/registry.py 의 FLOWS 에 이름으로 등록되어 start 때 꺼내짐
│  │  │  ├─ ref.py                         # 단위가 코드를 이름으로 가리키는 값. 예: Ref("answer_is", {"value": "예"}) → 조건 함수 answer_is(value="예"). state.json 에도 그대로 저장되어 다음 명령이 같은 함수를 다시 찾음
│  │  │  ├─ run_condition.py               # 조건 함수가 지켜야 하는 모양: FlowContext 를 받아 실행할지(bool)를 돌려줌
│  │  │  ├─ items_source.py                # 반복 항목 함수가 지켜야 하는 모양: FlowContext 를 받아 반복할 항목 목록을 돌려줌
│  │  │  ├─ unit/
│  │  │  │  ├─ unit.py                     # TaskUnit, GroupUnit 의 공통 부모. 만들자마자 검사: 이름은 영문 소문자·숫자·_ 만 (노드 폴더 이름이 되므로), 그 밖은 종류별 검사 (예: 묶음 안 자식 이름이 겹치면 실패)
│  │  │  │  ├─ task_unit.py                # 선언 트리의 끝 단위. 어떤 Task 를, 어느 수행자가, 어떤 조건에서 실행할지
│  │  │  │  ├─ group_unit.py               # 자식 단위를 묶는 단위. 차례대로 돌릴지, 반복 항목마다 돌릴지
│  │  │  │  └─ builders.py                 # task(...), group(...): 선언을 짧게 쓰는 함수. 1.2 절의 DEMO_FLOW 처럼 씀
│  │  │  ├─ task/
│  │  │  │  ├─ task.py                     # 워크플로가 상속하는 부모 클래스. 요청 종류와 결과 종류를 적고, 요청 만들기(build_request)와 결과 만들기(build_output)를 구현함
│  │  │  │  ├─ output_kind.py              # 결과 종류: DATA(dict, result.json 에 저장), FILES(텍스트 파일, 산출물 폴더에 저장). 읽는 쪽은 이것을 보고 읽는 방법을 고름
│  │  │  │  ├─ task_output.py              # Task 가 돌려주는 노드의 결과. DATA 면 data(dict), FILES 면 files(파일 이름 → 내용). 뒤 노드가 읽음
│  │  │  │  ├─ reply_rejected_error.py     # Task 가 메인 세션의 답을 거절할 때 던짐 (예: 선택지 밖의 답). 실행기가 같은 질문을 다시 냄
│  │  │  │  └─ output_missing_error.py     # 읽으려는 노드에 결과가 없을 때 (예: run_if 로 건너뛴 노드). 조건 함수가 잡아서 거짓으로 처리하기도 함
│  │  │  └─ context/
│  │  │     ├─ flow_context.py             # Task·조건·반복 항목 함수가 받는 실행 정보. 앞 노드 결과를 노드 이름으로 읽고(read), 산출물 폴더를 얻고(output_dir), 지금 반복 항목을 얻음(current_item)
│  │  │     ├─ node_locator.py             # read 가 노드 이름으로 시나리오에서 노드를 찾을 때 씀
│  │  │     └─ find_item.py                # current_item 의 실제 구현. 항목 번호 "2.1" 같은 것을 보고 저장된 항목 목록에서 내용을 찾아 줌
│  │  ├─ registry/
│  │  │  ├─ registry.py                    # 키로 코드를 등록하고 찾는 목록의 인터페이스. 등록은 import 할 때, 찾기는 명령마다
│  │  │  ├─ in_memory_registry.py          # 위 인터페이스의 구현. 같은 키를 두 번 등록하면 오류로 막음
│  │  │  └─ registries.py                  # TASKS, CONDITIONS, ITEM_SOURCES: 워크플로가 @TASKS.register_as("키") 처럼 등록하는 곳
│  │  ├─ request/                          # Task 가 수행자에게 "이렇게 해 달라"고 넘기는 내용. 수행자마다 받는 종류가 하나
│  │  │  ├─ task_request.py                # 아래 6개를 합친 타입. Task.build_request 의 반환 타입
│  │  │  ├─ code_request.py                # CODE 용. 넘길 내용이 없음 (일은 Task.build_output 에서 함)
│  │  │  ├─ prompt_request.py              # CLAUDE_P 용. 어떤 프롬프트(PromptSpec)에 어떤 입력 글을 넣을지
│  │  │  ├─ show_request.py                # MAIN_SESSION_SHOW 용. 사용자에게 보일 글
│  │  │  ├─ question_request.py            # MAIN_SESSION_ASK 용. 질문과 선택지
│  │  │  ├─ conversation_request.py        # MAIN_SESSION_TALK 용. 대화의 목표와 첫 말
│  │  │  └─ subagent_request.py            # SUBAGENT 용. 띄울 에이전트 이름, 넘길 메시지, 결과를 쓸 파일
│  │  ├─ instruction/
│  │  │  ├─ instruction.py                 # CLI 가 메인 세션에 돌려주는 할 일 하나. 요청에 노드 uuid 와 항목 번호를 붙인 것
│  │  │  ├─ instruction_type.py            # 할 일의 종류: show, ask, talk, spawn, finished, failed. run 스킬 글이 종류마다 처리 방법을 적음
│  │  │  └─ instruction_converter.py       # 지시를 JSON 으로 바꿈. CLI 출력과, 답을 기다리는 동안 state.json 에 저장할 때 씀
│  │  ├─ performer/                        # 요청을 실제로 처리하는 쪽
│  │  │  ├─ performed_by.py                # 수행자 종류: CODE, CLAUDE_P, MAIN_SESSION_SHOW, MAIN_SESSION_ASK, MAIN_SESSION_TALK, SUBAGENT
│  │  │  ├─ task_performer.py              # 수행자 인터페이스. 처리하기(perform)와, 메인 세션의 답을 받아 반환값으로 바꾸기(receive_reply)
│  │  │  ├─ accepts.py                     # 수행자마다 받는 요청 종류 표. 시작 전 검사가 Task 의 요청 종류와 맞는지 볼 때 씀
│  │  │  ├─ call_outcome.py                # claude -p 를 부른 결과 묶음: 출력, 호출 기록 위치, 비용, 시간. 실행기가 history.jsonl 에 옮겨 적음
│  │  │  ├─ default_performers.py          # 수행자 6개를 만들어 종류별로 묶음. cli.py 가 실행기를 조립할 때 부름
│  │  │  ├─ code/code_performer.py         # CODE: 아무것도 하지 않고 바로 끝냄. 실제 일은 Task.build_output 이 함
│  │  │  ├─ claude_prompt/
│  │  │  │  ├─ claude_prompt_performer.py  # CLAUDE_P: claude -p 를 부르고, 성공이든 실패든 호출 기록을 노드 폴더 calls/ 에 저장
│  │  │  │  └─ recorded_prompt_call_error.py  # claude -p 가 실패했지만 호출 기록은 저장해 둔 상태. 실행기가 비용·시간을 history.jsonl 에 남김
│  │  │  ├─ main_session/
│  │  │  │  ├─ main_session_performer.py   # 메인 세션에 맡기는 수행자들의 공통 부모. 요청을 지시로 바꿔 돌려줌
│  │  │  │  ├─ main_session_show_performer.py  # SHOW: 글을 보이게 함. 답을 기다리지 않고 바로 끝남
│  │  │  │  ├─ main_session_ask_performer.py   # ASK: 선택지로 묻게 함. 빈 답이 오면 다시 물음
│  │  │  │  └─ main_session_talk_performer.py  # TALK: 사용자와 대화하게 함. 끝나면 대화 구간(시작·끝 시각)과 대화 기록 파일 경로를 돌려줘 뒤 노드가 대화 내용을 읽게 함
│  │  │  └─ subagent/subagent_performer.py # SUBAGENT: 서브에이전트를 띄우게 함. done 을 받으면 끝. 산출물 폴더의 파일은 실행기가 결과로 모음
│  │  ├─ runner/
│  │  │  ├─ flow/
│  │  │  │  ├─ flow_runner.py              # 명령 단위 실행기의 인터페이스. start, next, done, status, cancel 에 하나씩 대응
│  │  │  │  ├─ default_flow_runner.py      # 위의 구현. 어느 실행인지 찾고, state.json 을 읽고 쓰고, 시작·끝·실패 회복을 처리. 노드 일은 UnitRunner 에 맡김
│  │  │  │  ├─ flow_registry.py            # 워크플로 이름으로 FlowDefinition 을 찾는 인터페이스. start demo 의 "demo" 를 찾음
│  │  │  │  └─ dict_flow_registry.py       # 위의 구현. workflow/registry.py 의 FLOWS dict 를 그대로 씀
│  │  │  ├─ unit/
│  │  │  │  ├─ unit_runner.py              # 노드 단위 실행기의 인터페이스. 다음 할 일 내기(next_instruction)와 답 넣기(submit_reply)
│  │  │  │  ├─ default_unit_runner.py      # 위의 구현. 3.2·3.3 절의 일을 실제로 함: 수행할 노드 찾기, 수행자에게 넘기기, 결과 저장, 답 기다리기, 실패 기록
│  │  │  │  └─ scenario_status.py          # 노드 트리를 보고 바꾸는 작은 함수들: 이 노드가 끝났나, 실패한 노드 되돌리기, 반복이 끝나면 안쪽 노드 정리
│  │  │  ├─ child_run/
│  │  │  │  ├─ child_run.py                # 묶음이 자식을 돌리는 방식: IN_ORDER(차례대로), FOR_EACH_ITEM(항목마다)
│  │  │  │  ├─ child_run_strategy.py       # 방식마다 "다음에 볼 자식과 그 항목 번호"를 차례로 내주는 인터페이스
│  │  │  │  ├─ in_order_strategy.py        # IN_ORDER: 자식을 위에서부터 하나씩, 항목 번호는 부모 것 그대로
│  │  │  │  ├─ for_each_item_strategy.py   # FOR_EACH_ITEM: 항목마다 자식 전체를, 항목 번호 "1", "2", "2.1" 을 붙여서. 가장 바깥 반복은 항목을 items.json 에 저장해 두고 씀
│  │  │  │  └─ default_strategies.py       # 두 방식을 만들어 묶음. cli.py 가 실행기를 조립할 때 부름
│  │  │  └─ scenario/
│  │  │     ├─ check_definition.py         # start 때 실행을 만들기 전에 선언을 검사: 키가 등록돼 있나, 수행자가 Task 의 요청 종류를 받나
│  │  │     └─ build_scenario.py           # start 때 선언을 본떠 ScenarioNode 트리를 만듦. 노드마다 uuid 를 붙이고 상태를 PENDING 으로
│  │  ├─ model/                            # 파일로 저장되는 실행 데이터 (4.1 절)
│  │  │  ├─ session/claude_session.py      # session.json 의 내용. next·done 이 이어서 할 실행 id, TALK 가 읽을 대화 기록 경로
│  │  │  ├─ run_state/
│  │  │  │  ├─ flow_run_state.py           # state.json 의 내용. 실행 상태, 노드 트리, 답을 기다리는 지시. 명령마다 이것 하나를 읽고 씀
│  │  │  │  ├─ flow_run_status.py          # 실행 하나의 상태: 진행 중, 실패, 끝남, 취소
│  │  │  │  ├─ scenario_node.py            # 노드 하나. 선언에서 복사한 내용(Task 키, 수행자, 조건)과 진행 상황(상태, 끝난 항목, 기다리는 항목)
│  │  │  │  ├─ node_kind.py                # 노드가 TaskUnit 에서 왔는지(TASK), GroupUnit 에서 왔는지(GROUP)
│  │  │  │  └─ node_status.py              # 노드 상태: 대기, 진행 중(묶음), 답을 기다림, 끝남, 건너뜀, 실패
│  │  │  ├─ history/history_entry.py       # history.jsonl 한 줄. 언제, 어느 노드·항목이, 어떤 상태가 됐는지와 비용·시간·실패 내용
│  │  │  └─ result/
│  │  │     ├─ node_result.py              # result.json 의 내용. 항목 번호 → 그 항목의 결과
│  │  │     ├─ fixed_items.py              # items.json 의 내용. 처음 계산해 저장해 둔 반복 항목과 저장 시각
│  │  │     └─ item_key.py                 # 반복 밖 노드가 쓰는 항목 번호 "-"
│  │  ├─ port/                             # 실행 데이터를 파일에 읽고 쓰는 곳 (4.3 절)
│  │  │  ├─ run_location.py                # 세션 폴더, 실행 폴더, 노드 폴더, 산출물 폴더의 경로를 정함. 경로 규칙이 바뀌면 여기만 고침
│  │  │  ├─ session/                       # session.json 읽기·쓰기 인터페이스와 구현, JSON 변환기
│  │  │  ├─ run_state/                     # state.json 읽기·쓰기 인터페이스와 구현, JSON 변환기
│  │  │  ├─ history/                       # history.jsonl 읽기·덧붙이기 인터페이스와 구현, JSON 변환기
│  │  │  └─ result/                        # 노드 폴더(result.json, files/, items.json, calls/) 읽기·쓰기 인터페이스와 구현, JSON 변환기 3개
│  │  ├─ hook/
│  │  │  ├─ session_start_hook.py          # Claude Code 세션이 열릴 때 그 세션의 대화 기록 파일 경로를 session.json 에 적음. TALK 뒤 노드가 대화를 읽으려면 필요
│  │  │  └─ stop_hook.py                   # 실행이 진행 중인데 메인 세션이 지시를 다 처리하지 않고 멈추려 하면 막고 next 를 부르라고 알림
│  │  └─ builtin/
│  │     └─ answer_is.py                   # 어느 워크플로에서나 쓰는 조건 함수: 앞 노드의 답이 value 와 같은가. demo 의 confirm_each 가 씀
│  ├─ claude_utils/                        # Claude 와 관련된 기능. engine 이 쓰지만 engine 을 모름
│  │  ├─ prompt/
│  │  │  ├─ call_prompt.py                 # claude -p 를 한 번 부름. 빈 임시 폴더에서 도구 없이 실행하고, 출력 데이터 클래스 객체와 호출 기록을 돌려줌
│  │  │  ├─ prompt_output_converter.py     # 출력 데이터 클래스로 claude -p 에 넘길 JSON 스키마를 만들고, 받은 JSON 을 그 클래스로 바꿈
│  │  │  ├─ claude_cli_error.py            # claude CLI 가 실패했을 때의 공통 부모 예외
│  │  │  ├─ prompt_call_error.py           # claude -p 실패 (종료 코드, 시간 초과, 출력 형식). 실패한 호출의 기록 전체를 담아 비용을 잃지 않게 함
│  │  │  ├─ common/prompt_file.py          # claude -p 가 돌려주는 파일 하나(이름, 내용). 결과가 파일인 프롬프트는 출력 데이터 클래스에 list[PromptFile] 필드를 둠
│  │  │  └─ dto/
│  │  │     ├─ prompt_spec.py              # 프롬프트 하나의 설정: 프롬프트 파일, 출력 데이터 클래스, 모델, 시간 제한. 워크플로가 claude -p 작업의 _task.py 안에 하나씩 만듦
│  │  │     └─ prompt_call_record.py       # 호출 하나의 기록: 보낸 것(프롬프트, 입력)과 받은 것(출력, 비용, 시간)
│  │  └─ transcript/
│  │     ├─ read_dialogue.py               # Claude Code 대화 기록 파일(JSONL)에서 도구 호출·스킬 본문 등을 빼고 사용자와 Claude 가 직접 주고받은 말만 뽑음
│  │     └─ dto/utterance.py               # 뽑은 말 하나: 누가(사용자/Claude), 언제, 무엇을
│  ├─ common/                              # engine 과 port 가 같이 쓰는 작은 도구
│  │  ├─ files.py                          # 파일 쓰기를 임시 파일에 먼저 쓰고 이름을 바꾸는 방식으로 해서, 중간에 끊겨도 반쯤 쓴 파일이 남지 않게 함. JSON·JSONL 읽기·쓰기
│  │  ├─ paths.py                          # 실행 데이터를 둘 폴더: 작업 폴더의 .package/, 시험할 때는 환경 변수 PACKAGE_HOME
│  │  └─ clock.py                          # 기록에 남길 지금 시각 (UTC, 초 단위)
│  ├─ workflow/
│  │  ├─ registry.py                       # FLOWS: start 에 넘기는 워크플로 이름과 FlowDefinition 의 짝. 새 워크플로를 만들면 여기 추가
│  │  ├─ demo/                             # 예시 워크플로: 단위 트리의 세 가지 실행 방식(차례대로, 조건, 반복). 아래 5.2 절
│  │  └─ count_joke/                       # 예시 워크플로: 코드 실행 → LLM 호출 → 서브에이전트 → 보이기. docs/workflow.md 6 절
│  ├─ model/                               # 프로젝트의 도메인 데이터. 예시로 count_joke 가 쓰는 counter/ 가 있음
│  └─ port/                                # 프로젝트가 바깥 API·파일을 다루는 곳. 예시로 counter 를 파일에 읽고 쓰는 local/counter/ 가 있음
└─ tests/
   ├─ conftest.py                          # 모든 시험이 임시 폴더를 PACKAGE_HOME 으로 써서 실제 .package/ 를 건드리지 않게 함
   ├─ test_cli.py                          # 실제 사용처럼 CLI 명령과 훅을 차례로 불러 demo 를 끝까지 돌림
   ├─ model/test_counter.py                # Counter.up() 이 새 값을 돌려주고 자신은 그대로인지
   ├─ port/test_counter_port.py            # 카운터 파일이 없을 때 0, 저장한 값을 다시 읽는지
   ├─ workflow/test_count_joke.py          # 가짜 claude 로 count_joke 를 끝까지: 카운터 증가, 프롬프트 입력, 서브에이전트 산출물 폴더, 보이기, 빈 폴더 경고
   ├─ engine/
   │  ├─ test_definition.py                # 잘못된 선언이 만들 때·시작 전에 막히는지(이름 겹침, reads), 레지스트리, read 가 항목 번호를 맞게 고르고 파일 결과를 읽는지
   │  ├─ test_runner_v2.py                 # 실행기로 demo 를 끝까지, 실패한 노드를 다시 하기, 반복 안의 반복, 서브에이전트·claude -p 의 파일 결과
   │  ├─ test_flow_specs.py                # 변환기로 저장했다가 다시 읽어도 같은 데이터가 나오는지
   │  └─ test_engine_port.py               # 파일이 4.1 절의 위치와 이름으로 저장되는지
   ├─ claude_utils/
   │  ├─ test_call_prompt.py               # 가짜 claude 로 성공, 오류 응답, 시간 초과를 흉내 내 호출 기록이 남는지
   │  └─ test_read_dialogue.py             # 대화 기록에서 사용자와 Claude 의 직접 대화만 뽑히는지
   └─ fixtures/transcripts/demo_run.jsonl  # test_read_dialogue 가 읽는 입력. demo 를 실제로 돌린 대화 기록에서 필요한 필드만 남김
```

### 5.2 demo 워크플로 (`workflow/demo/`)

폴더는 `DEMO_FLOW` 의 단위 트리와 같은 모양입니다. 폴더 이름이 곧 노드 이름이라, 노드 경로 `check/confirm_each/confirm` 이 파일 경로와 같습니다.
이름에는 순서 번호를 붙이지 않습니다. 실행 순서는 `demo_flow.py` 한 곳에서 봅니다.

```
workflow/demo/
├─ demo_flow.py                    # DEMO_FLOW 선언. 순서·조건·반복을 여기서 정하고, 아래 파일들을 import 해서 등록
├─ hello/
│  └─ hello_task.py                # HelloTask "demo.hello": 시작한다고 보임 (SHOW)
├─ talk/                           # 묶음: 대화로 듣고 목록으로 정리
│  ├─ listen/
│  │  └─ listen_task.py            # ListenTask "demo.listen": 좋아하는 과일을 대화로 들음 (TALK). 결과는 대화 구간과 대화 기록 경로
│  └─ collect_fruits/
│     └─ collect_fruits_task.py    # CollectFruitsTask "demo.collect_fruits": 과일 목록을 결과로 남김 (CODE)
├─ check/                          # 묶음: 확인할지 묻고, 그렇다면 과일마다 확인
│  ├─ choose_task.py               # ChooseTask: 아래 두 묻기 작업의 부모. 선택지 밖의 답이면 ReplyRejectedError 로 다시 물음
│  ├─ ask_check/
│  │  └─ ask_check_task.py         # AskCheckTask "demo.ask_check": "과일마다 확인할까요?" (ASK, 예 / 아니요)
│  └─ confirm_each/                # 반복 묶음: ask_check 의 답이 "예"일 때만, 과일마다
│     ├─ fruits_items.py           # fruits "demo.fruits": 반복 항목. collect_fruits 의 결과에서 과일 목록을 읽음
│     └─ confirm/
│        └─ confirm_task.py        # ConfirmTask "demo.confirm": "<지금 과일> 맞나요?" (ASK, 맞음 / 아님)
└─ bye/
   └─ bye_task.py                  # ByeTask "demo.bye": 끝났다고 보임 (SHOW)
```

- 여러 노드가 같이 쓰는 코드(`choose_task.py`)는 그 노드들을 묶은 폴더(`check/`)에 둡니다.
- 반복 항목 함수는 그 반복 묶음의 폴더(`confirm_each/`)에 둡니다.
- 조건 `answer_is` 는 engine 의 기본 조건이라 demo 에 없습니다. `demo_flow.py` 가 `engine/builtin/answer_is.py` 를 import 해서 등록합니다.

## 6. 주의 사항

- engine 과, 초기화 스킬이 함께 복사한 패키지(`claude_utils`, `entry`, `common` 에 처음부터 있는 파일)는 가능하면 바꾸지 않습니다.
- 새로운 워크플로는 `workflow/` 아래에 만듭니다. 제작과 선언 규칙은 `docs/workflow.md` 를 참고합니다.

---

## 부록: 정한 것 (2026-11-15)

- engine 의 실행 데이터도 model / port 규칙을 따른다. 프로젝트의 `model/`, `port/` 와 별개로 `engine/model/`, `engine/port/` 에 둔다.
- 파일에 저장하는 JSON 형식은 데이터 클래스에 두지 않는다. 저장 파일 종류마다 변환기 클래스를 그 포트 폴더에 두고, 메서드는 `to_file` / `to_data` 다.
- enum 은 그것이 설명하는 데이터나 기능 옆에 둔다. 한 줄 설명과 예시로 지시한다. 예: `PerformedBy` 는 `performer/`, `NodeStatus` 는 `model/run_state/`.
- 예외 이름은 `Error` 로 끝낸다. claude -p 실패는 `PromptCallError`(claude_utils, 호출 기록 전체)와 `RecordedPromptCallError`(engine, 저장 위치·비용·시간)로 나눈다.
- claude -p 실행과 그 입출력 스펙은 `claude_utils/prompt/`, 파일 쓰기·데이터 폴더 위치·시각은 `common/` 에 둔다. 초기화 스킬도 이 위치로 복사한다.
- 원본 패키지 이름은 `package`. 원본은 이 레포의 `template/src/package/engine/`.
