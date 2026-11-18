---
name: tool-add-port
description: port 패키지에 바깥 데이터(로컬 파일, 바깥 API)를 다루는 인터페이스와 구현을 만들거나 바꾼다. 포트마다 폴더를 두고 Reader / Writer 인터페이스, default_ 구현, JSON 변환기, 위치 또는 dto 를 각각 파일로 쓴다. 다루는 model 이 없으면 먼저 tool-add-model 이 필요하다고 알린다. planner 의 계획서나 사용자 요청을 받아 작업한다.
---

# tool-add-port

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 port 패키지를 다루는 스킬이다.
프로젝트는 entry(CLI 진입점), engine(워크플로 실행 엔진), workflow(기능 구현), model(도메인 데이터), port(바깥 데이터 접근), claude_utils(Claude 관련 기능), common(공통 기능)으로 나뉜다.
port 는 바깥 데이터를 다루는 곳이다. 바깥 API 호출과, model 을 파일로 저장하고 읽는 일이 여기에 있다. 워크플로의 단계는 바깥 데이터를 port 를 거쳐서만 읽고 쓴다. 그래서 바깥이 바뀌어도 고칠 곳이 포트 하나로 모인다.
이 스킬은 `tool-planner` 가 계획서를 확인받은 뒤 부르거나, 사용자가 직접 부른다. 다루는 model 이 없으면 `tool-add-model` 이 먼저다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/docs/engine.md` 5.1 절(프로젝트 전체 트리).

## 1. 이 스킬의 목적

`src/{pkg}/port/` 에 바깥 데이터를 읽고 쓰는 포트를 만들거나 바꾼다.

- **입력**: planner 계획서의 port 항목, 또는 사용자 요청. 아래가 들어 있어야 한다. 빠진 것이 있으면 묻는다.
  - 대상: 로컬 파일(무엇을 어디에 저장하는지) 또는 바깥 API(서비스, 호출할 엔드포인트, 인증 방법)
  - 동작: 읽기만인지, 쓰기도 있는지. 메서드마다 받는 값과 돌려주는 값
  - 다루는 데이터: 어떤 model 클래스인지, 또는 그 포트만 아는 스펙(dto)인지
- **만드는 것**: 인터페이스, 구현, 변환기, 위치(파일 포트) 또는 dto(API 포트), 그 포트의 예외, 시험, `specs/ports.md` 갱신
- **만들지 않는 것**: model 클래스(`tool-add-model`), 워크플로, 포트를 쓰는 쪽의 코드

`{pkg}` 는 `src/` 아래에 있는 유일한 폴더 이름이다.

## 2. 이 모듈의 목적과 형태

port 는 바깥 데이터를 다루는 곳이다. 바깥 API 를 부르는 것, model 을 파일로 저장하고 읽는 것이 여기에 들어간다.
워크플로와 다른 코드는 바깥 데이터를 port 를 거쳐서만 다룬다.

- 포트마다 폴더 하나. 로컬 파일 포트는 `local/` 아래에 모은다.
- 인터페이스, 구현, 변환기, dto 는 각각 별도 파일. 클래스 하나에 파일 하나.
- 읽기만 하면 Reader 만 둔다. 쓰기가 있으면 Writer 를 더한다.
- 구현 이름은 `Default` 로 시작한다.
- 데이터의 JSON 모양은 model 이 아니라 포트의 변환기가 안다.
- port 는 `model` 과 `common` 만 import 한다 (import 검사 계약).

## 3. 대표 트리와 파일 예시

```
port/
├─ local/counter/                  # 로컬 파일 포트 (원본에 있음)
│  ├─ counter_reader.py            # 인터페이스: 읽기
│  ├─ counter_writer.py            # 인터페이스: 쓰기
│  ├─ default_counter_reader.py    # 구현: 파일에서 읽음
│  ├─ default_counter_writer.py    # 구현: 파일에 씀
│  ├─ counter_file_converter.py    # Counter ↔ 파일의 JSON
│  └─ counter_file.py              # 파일 위치
└─ gh/                             # 바깥 API 포트 (예시)
   ├─ gh_reader.py                 # 인터페이스: 읽기
   ├─ default_gh_reader.py         # 구현: gh CLI 로 GitHub API 호출
   ├─ gh_api_converter.py          # API 응답 JSON → dto
   ├─ gh_api_error.py              # 호출 실패
   └─ dto/
      └─ gh_repo_info.py           # API 응답 중 우리가 쓰는 부분
```

### 3.1 로컬 파일 포트 (`local/counter/`, 원본에 있음)

```python
# counter_reader.py
class CounterReader(ABC):
    @abstractmethod
    def read(self) -> Counter:
        """저장된 카운터. 없으면 0."""

# counter_writer.py
class CounterWriter(ABC):
    @abstractmethod
    def save(self, counter: Counter) -> None: ...

# counter_file.py
def counter_file() -> Path:
    return home() / "counter.json"            # common.paths.home(): 데이터 폴더

# counter_file_converter.py
class CounterFileConverter:
    def to_file(self, c: Counter) -> dict[str, Any]:
        return {"value": c.value}

    def to_data(self, d: dict[str, Any]) -> Counter:
        return Counter(int(d["value"]))

# default_counter_reader.py
class DefaultCounterReader(CounterReader):
    def read(self) -> Counter:
        p = counter_file()
        return CounterFileConverter().to_data(files.read_json(p)) if p.exists() else Counter(0)

# default_counter_writer.py
class DefaultCounterWriter(CounterWriter):
    def save(self, counter: Counter) -> None:
        files.write_json(counter_file(), CounterFileConverter().to_file(counter))   # common.files: 원자적 쓰기
```

### 3.2 바깥 API 포트 (`gh/`, 예시)

GitHub 저장소 정보를 읽는다. `gh` CLI 로 호출하므로 새 의존성이 없고, 인증은 `gh` 가 맡는다.

```python
# dto/gh_repo_info.py: API 응답 중 우리가 쓰는 필드만
@dataclass(frozen=True, slots=True)
class GhRepoInfo:
    full_name: str
    default_branch: str
    open_issues: int

# gh_api_error.py
class GhApiError(RuntimeError):
    """gh api 호출 실패. 명령, 종료 코드, 오류 출력을 담는다."""

# gh_reader.py
class GhReader(ABC):
    @abstractmethod
    def get_repo(self, owner: str, name: str) -> GhRepoInfo:
        """저장소 정보. 없거나 권한이 없으면 GhApiError."""

# gh_api_converter.py
class GhApiConverter:
    def to_repo_info(self, body: dict[str, Any]) -> GhRepoInfo:
        return GhRepoInfo(body["full_name"], body["default_branch"], int(body["open_issues_count"]))

# default_gh_reader.py
class DefaultGhReader(GhReader):
    def get_repo(self, owner: str, name: str) -> GhRepoInfo:
        return GhApiConverter().to_repo_info(_gh_api(f"repos/{owner}/{name}"))


def _gh_api(path: str) -> dict[str, Any]:
    argv = [os.environ.get("{PKG}_GH_BIN", "gh"), "api", path]   # 시험에서는 가짜 gh 로 바꿈
    done = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    if done.returncode != 0:
        raise GhApiError(f"{' '.join(argv)} 실패 ({done.returncode}): {done.stderr.strip()}")
    return dict(json.loads(done.stdout))
```

## 4. 구현 규칙

**인터페이스**

- `ABC` 와 `@abstractmethod`. 메서드마다 한 줄 docstring 으로 무엇을 돌려주는지와, 없을 때·실패할 때의 동작을 적는다. **이유**: 쓰는 쪽은 인터페이스만 읽고 쓴다.
- 메서드 이름은 하는 일로 짓는다: 파일 포트는 `read`, `read_all`, `save`, `save_all`. API 포트는 그 API 의 동작으로(`get_repo`, `list_issues`, `create_issue`).
- 돌려주는 값은 model 이나 dto 다. `dict` 나 API 응답을 그대로 돌려주지 않는다.

**model 과 dto**

- 우리가 주로 다루는 데이터(도메인 데이터)면 model 을 쓴다. 없으면 먼저 `tool-add-model` 이 필요하다고 알리고 멈춘다.
- API 의 응답 모양처럼 주체는 아니지만 가지고 있어야 하는 스펙은 그 포트의 `dto/` 에 둔다. dto 도 `@dataclass(frozen=True, slots=True)`.
- dto 에는 우리가 쓰는 필드만 둔다. 응답 전체를 옮기지 않는다.

**변환기**

- 파일 포트: `{대상}_file_converter.py`, 메서드는 `to_file(model) -> dict`, `to_data(dict) -> model`.
- API 포트: `{서비스}_api_converter.py`, 응답을 바꾸는 메서드는 `to_{dto 이름}(body) -> dto`, 요청 본문을 만드는 메서드는 `to_{요청 이름}_body(...) -> dict`.
- 변환기 밖에서 JSON 키를 다루지 않는다.

**구현**

- 파일 포트: 경로는 `{대상}_file.py` 한 곳에서 정하고 `common.paths.home()` 아래에 둔다. 쓰기는 `common.files` 의 함수를 쓴다(임시 파일에 쓰고 이름을 바꾸는 원자적 쓰기).
- API 포트:
  - 새 라이브러리 없이 되면 그렇게 한다 (표준 라이브러리, `gh` 같은 CLI). 라이브러리가 필요하면 사용자에게 확인받고 `pyproject.toml` 에 더한다.
  - 시간 제한을 둔다.
  - 실패는 그 포트의 예외(`{서비스}_api_error.py`)로 던진다. 메시지에 무엇을 불렀고 무엇이 돌아왔는지 적는다.
  - 실행 파일·주소·토큰은 환경 변수로 바꿀 수 있게 한다 (`{PKG}_{서비스}_BIN`, `{PKG}_{서비스}_URL`, `{PKG}_{서비스}_TOKEN`). 토큰을 코드나 파일에 적지 않는다.
- 쓰기는 같은 값으로 두 번 불러도 결과가 같게 만든다(덮어쓰기, 같은 id 면 갱신). **이유**: 워크플로의 단계는 실패하면 다시 수행되므로, 같은 쓰기가 두 번 일어날 수 있다.

**금지**

- `engine`, `workflow`, `claude_utils` 를 import 하지 않는다.
- 포트 폴더 밖(`model/`, `common/`)에 이 포트만 쓰는 코드를 두지 않는다.
- 시험에서 진짜 바깥 API 를 부르지 않는다.

## 5. 있는 것 먼저 확인

1. `specs/ports.md` 와 `src/{pkg}/port/` 를 읽고 같은 대상의 포트가 있는지 본다.
   - 있고 메서드도 있으면: 만들지 않는다. 있는 메서드를 알려 준다.
   - 있고 메서드만 없으면: 그 포트의 인터페이스에 메서드를 더하고, 모든 구현에 같이 더한다.
   - 없으면: 새 폴더를 만든다.
2. 다루는 model 이 `specs/models.md` 에 있는지 본다. 없으면 `tool-add-model` 이 먼저 필요하다고 알린다.
3. 기존 메서드의 이름·인자·돌려주는 값을 바꿀 때, 그리고 파일 저장 모양(변환기)을 바꿀 때는 바꾸기 전과 후를 보여 주고 확인받는다. 쓰는 곳을 `grep` 으로 모두 찾아 함께 보여 준다. 저장 모양이 바뀌면 이미 저장된 파일을 읽지 못할 수 있다는 것도 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/port tests/port
uv run lint-imports                 # port 가 engine·workflow·claude_utils 를 import 하면 여기서 실패
uv run mypy
uv run pytest -q tests/port
```

시험은 `tests/port/{포트 이름}/` 에 둔다.

- 파일 포트: 저장한 값을 다시 읽으면 같은지, 파일이 없을 때 정한 대로 동작하는지. 시험은 임시 폴더를 데이터 폴더로 쓴다(`tests/conftest.py` 가 `{PKG}_HOME` 을 바꿈).
- API 포트: 가짜 실행 파일이나 가짜 응답으로 성공과 실패를 하나씩. 진짜 API 는 부르지 않는다.

```python
def test_should_read_repo_info_from_gh_api(tmp_path, monkeypatch):
    fake = tmp_path / "gh"
    fake.write_text('#!/bin/bash\necho \'{"full_name": "octo/hello", "default_branch": "main", "open_issues_count": 3}\'')
    fake.chmod(0o755)
    monkeypatch.setenv("{PKG}_GH_BIN", str(fake))
    assert DefaultGhReader().get_repo("octo", "hello") == GhRepoInfo("octo/hello", "main", 3)
```

하나라도 실패하면 고친 뒤 다시 돌린다. 통과하기 전에는 끝내지 않는다.

## 7. 산출물

- 만들거나 바꾼 파일 목록
- 바꾼 경우: 바꾸기 전과 후, 영향을 받는 파일
- 새로 더한 환경 변수와 의존성
- `specs/ports.md` 갱신 (없으면 만든다). 워크플로를 만드는 스킬은 이 문서를 보고 포트를 쓴다.

```markdown
## gh (`port/gh/`)
바깥 API: GitHub (gh CLI). 환경 변수: `{PKG}_GH_BIN`

| 인터페이스 | 메서드 | 돌려주는 값 | 없을 때·실패 |
|---|---|---|---|
| GhReader | get_repo(owner, name) | GhRepoInfo | GhApiError |

dto: `GhRepoInfo(full_name, default_branch, open_issues)`
```
