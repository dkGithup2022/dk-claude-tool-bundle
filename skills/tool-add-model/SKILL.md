---
name: tool-add-model
description: model 패키지에 도메인 데이터 클래스를 만들거나 바꾼다. 불변 데이터 클래스, 묶이는 정보는 도메인 폴더 안의 별도 클래스, 값이 정해진 것은 enum 으로 쓴다. 파일 저장 모양(JSON)은 만들지 않는다(포트의 일). planner 의 계획서나 사용자 요청을 받아 작업한다.
---

# tool-add-model

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 model 패키지를 다루는 스킬이다.
프로젝트는 entry(CLI 진입점), engine(워크플로 실행 엔진), workflow(기능 구현), model(도메인 데이터), port(바깥 데이터 접근), claude_utils(Claude 관련 기능), common(공통 기능)으로 나뉜다.
model 은 워크플로와 포트가 주로 다루는 데이터(일정, 사용자 같은 것)를 불변 데이터 클래스로 둔다. 다른 패키지를 쓰지 않는 가장 아래 층이라, 여러 곳이 같은 모양의 데이터를 믿고 쓸 수 있게 하는 기반이다.
이 스킬은 `tool-planner` 가 계획서를 확인받은 뒤 부르거나, 사용자가 직접 부른다. model 을 만든 뒤에는 대개 `tool-add-port` 가 그 model 을 저장하거나 읽는 포트를 만든다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/docs/engine.md` 5.1 절(프로젝트 전체 트리).

## 1. 이 스킬의 목적

`src/{pkg}/model/` 에 도메인 데이터 클래스를 만들거나 바꾼다.

- **입력**: planner 계획서의 model 항목, 또는 사용자 요청. 도메인 이름, 필드와 타입, 상태를 바꾸는 동작이 들어 있어야 한다. 빠진 것이 있으면 묻는다.
- **만드는 것**: 데이터 클래스, enum, 그 시험, `specs/models.md` 갱신
- **만들지 않는 것**: 파일·API 와 주고받는 JSON 모양(포트의 변환기가 맡음), 저장(포트), 워크플로의 결과 dict

`{pkg}` 는 `src/` 아래에 있는 유일한 폴더 이름이다.

## 2. 이 모듈의 목적과 형태

model 은 워크플로와 포트가 주로 다루는 데이터, 즉 도메인 데이터를 둔다. 예: 일정(todo), 사용자(user), 카운터(counter).
API 응답 모양이나 조인 결과처럼 주체가 아니지만 스펙으로 가지고 있어야 하는 것은 model 이 아니라 그 포트의 `dto/` 에 둔다.

- 도메인마다 폴더 하나. 한 폴더 아래에 계층 없이 모두 나열하지 않는다.
- 클래스 하나에 파일 하나.
- 모든 클래스는 불변이다. 값을 바꾸는 동작은 새 객체를 돌려준다.
- model 은 다른 패키지를 import 하지 않는다 (import 검사 계약). 시각이 필요하면 호출하는 쪽이 값을 넘긴다.

## 3. 대표 트리와 파일 예시

```
model/
├─ counter/
│  └─ counter.py              # 필드 하나, 동작 하나 (원본에 있음)
├─ user/
│  ├─ user.py                 # 주 클래스. 하위 정보를 필드로 가짐
│  └─ user_auth_info.py       # user 아래에 묶이는 하위 정보
└─ todo/
   ├─ todo.py                 # 주 클래스. enum 과 튜플 필드를 가짐
   └─ todo_status.py          # 값이 정해진 enum
```

**단순한 데이터와 동작** (`counter/counter.py`, 원본에 있음)

```python
@dataclass(frozen=True, slots=True)
class Counter:
    value: int

    def up(self) -> Counter:
        """1 늘린 새 Counter. 자신은 바꾸지 않는다."""
        return Counter(self.value + 1)
```

**하위 정보** (`user/user_auth_info.py`, `user/user.py`)

```python
@dataclass(frozen=True, slots=True)
class UserAuthInfo:
    provider: str              # "github"
    provider_user_id: str
    token_expires_at: str      # ISO 8601 UTC, 예: "2026-11-16T10:00:00Z"


@dataclass(frozen=True, slots=True)
class User:
    user_id: str
    name: str
    auth: UserAuthInfo | None = None

    def with_auth(self, auth: UserAuthInfo) -> User:
        return replace(self, auth=auth)
```

**enum** (`todo/todo_status.py`)

```python
class TodoStatus(StrEnum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"
```

**enum 과 튜플 필드를 가진 주 클래스** (`todo/todo.py`)

```python
@dataclass(frozen=True, slots=True)
class Todo:
    todo_id: str
    title: str
    when: str | None                       # ISO 8601. 날짜 없는 일정은 None
    updated_at: str
    alarms: tuple[str, ...] = ()           # 컬렉션은 tuple
    status: TodoStatus = TodoStatus.OPEN

    def mark_done(self, now: str) -> Todo:
        """끝난 일정으로. 시각은 호출하는 쪽이 넘긴다 (model 은 common.clock 을 import 하지 않음)."""
        return replace(self, status=TodoStatus.DONE, updated_at=now)
```

## 4. 구현 규칙

**클래스**

- `@dataclass(frozen=True, slots=True)` 로 쓴다. **이유**: 값이 중간에 바뀌지 않아야 워크플로의 단계가 같은 데이터를 믿고 읽는다. `slots` 는 없는 필드에 값을 넣는 실수를 막는다.
- `__init__` 을 직접 쓰지 않는다. 검사가 꼭 필요하면 `__post_init__` 에 최소로 둔다.
- 값을 바꾸는 동작은 `dataclasses.replace` 로 새 객체를 돌려준다. 반환 타입은 그 클래스.
- 동작 이름은 하는 일로 짓는다 (`up`, `mark_done`, `with_auth`). 일부 필드만 바꾸는 단순한 동작은 `with_{필드}`.
- 만들 때 계산이 필요하면(기본값을 채우거나 id 를 정하는 등) `@classmethod` 로 `create(...)` 를 둔다.

**필드**

- 컬렉션은 `tuple[T, ...]`. `list`, `dict` 는 불변이 깨지므로 쓰지 않는다.
- 값이 몇 개로 정해져 있으면 `StrEnum` (상태, 종류, 출처). 자유 입력이면 `str` (제목, 메모, URL). 애매하면 사용자에게 묻는다.
- enum 의 멤버 이름은 대문자, 값은 파일에 저장될 소문자 문자열.
- 시각은 ISO 8601 UTC 문자열(`"2026-11-16T10:00:00Z"`). 지금 시각은 호출하는 쪽이 `common.clock.utc_now()` 로 만들어 넘긴다.
- 비어도 되는 필드는 `X | None`. 기본값이 있는 필드는 기본값이 없는 필드 뒤에 둔다.

**묶기**

- 같은 뜻으로 묶이는 필드가 3개 이상이면 하위 정보 클래스로 뺀다. 파일 이름은 `{도메인}_{하위 정보}.py`, 같은 도메인 폴더에 둔다.
- 다른 도메인의 클래스를 필드로 쓸 수 있다 (model 안의 import 는 허용).

**금지**

- `to_dict`, `from_dict`, JSON 직렬화 코드를 두지 않는다. 파일·API 모양은 포트의 변환기가 맡는다.
- 다른 패키지(`common`, `port`, `engine`, `workflow`, 외부 라이브러리)를 import 하지 않는다.
- `datetime.now()` 를 부르지 않는다.
- 도메인 폴더 없이 `model/` 바로 아래에 파일을 두지 않는다.
- `__init__.py` 에서 다시 내보내지(re-export) 않는다. import 경로가 파일을 그대로 가리키게 한다.

## 5. 있는 것 먼저 확인

1. `specs/models.md` 와 `src/{pkg}/model/` 을 읽고, 같은 개념이 이미 있는지 본다.
   - 이미 있고 그대로 쓸 수 있으면: 만들지 않는다. 있는 클래스를 알려 준다.
   - 필드나 동작만 더하면 되면: 기존 클래스를 바꾼다 (아래 2).
   - 없으면: 새로 만든다.
2. 기존 클래스를 바꿀 때는 바꾸기 전과 후를 보여 주고 사용자에게 확인받는다.
   - 새 필드는 기본값과 함께 끝에 더한다. 위치 인자로 만드는 코드가 깨지지 않게 하기 위해서다.
   - 필드 이름을 바꾸거나 지우는 일은 이미 저장된 파일을 읽지 못하게 만들 수 있다. 그 클래스를 쓰는 포트 변환기와 워크플로를 `grep` 으로 모두 찾아 함께 보여 준다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/model tests/model
uv run lint-imports                 # model 이 다른 패키지를 import 하면 여기서 실패
uv run mypy
uv run pytest -q tests/model
```

값을 바꾸는 동작이 있으면 시험을 하나 둔다: `tests/model/{도메인}/test_{클래스 파일 이름}.py`.
새 객체를 돌려주는지, 원래 객체는 그대로인지를 본다.

```python
def test_should_return_new_counter_increased_by_one():
    c = Counter(7)
    assert c.up() == Counter(8) and c == Counter(7)
```

하나라도 실패하면 고친 뒤 다시 돌린다. 통과하기 전에는 끝내지 않는다.

## 7. 산출물

- 만들거나 바꾼 파일 목록
- 바꾼 경우: 바꾸기 전과 후, 영향을 받는 포트·워크플로 파일
- `specs/models.md` 갱신 (없으면 만든다). 다음 스킬(포트, 워크플로)은 이 문서를 보고 model 을 쓴다.

```markdown
## todo

### Todo (`model/todo/todo.py`)
| 필드 | 타입 | 뜻 |
|---|---|---|
| todo_id | str | |
| title | str | |
| when | str \| None | ISO 8601. 날짜 없는 일정은 None |
| status | TodoStatus | 기본 OPEN |

동작: `mark_done(now) -> Todo`

### TodoStatus (`model/todo/todo_status.py`)
OPEN = "open", DONE = "done", CANCELLED = "cancelled"
```
