---
name: tool-add-common
description: common 패키지에 여러 곳이 같이 쓰는 공통 기능(로깅, 파일 접근 같은 것)을 더한다. 한 곳에서만 쓰는 기능, 도메인 지식이 들어간 기능은 넣지 않는다. 이미 있는 파일(files.py, paths.py, clock.py)은 engine 이 쓰므로 고치지 않고 새 파일만 더한다.
---

# tool-add-common

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 common 패키지를 다루는 스킬이다.
프로젝트는 entry(CLI 진입점), engine(워크플로 실행 엔진), workflow(기능 구현), model(도메인 데이터), port(바깥 데이터 접근), claude_utils(Claude 관련 기능), common(공통 기능)으로 나뉜다.
common 은 여러 패키지가 같이 쓰는 공통 기능(로깅, 파일 접근 같은 것)을 둔다. engine 도 common 을 쓰므로, 처음부터 있는 파일은 고치지 않고 새 파일만 더한다.
이 스킬은 `tool-planner` 가 계획서를 확인받은 뒤 부르거나, 사용자가 직접 부른다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/docs/engine.md` 5.1 절(프로젝트 전체 트리).

## 1. 이 스킬의 목적

`src/{pkg}/common/` 에 공통 기능을 더한다.

- **입력**: planner 계획서의 common 항목, 또는 사용자 요청. 무슨 기능인지, 어디어디에서 쓸지가 들어 있어야 한다. 빠진 것이 있으면 묻는다.
- **만드는 것**: 공통 기능 파일, 그 시험
- **만들지 않는 것**: 한 곳에서만 쓰는 기능(그 곳에 둔다), 도메인 데이터(`model`), 바깥 데이터 접근(`port`)

`{pkg}` 는 `src/` 아래에 있는 유일한 폴더 이름이다.

## 2. 이 모듈의 목적과 형태

common 은 여러 패키지가 같이 쓰는 공통 기능을 둔다. 로깅, 파일 접근, 시각처럼 어느 기능에도 묶이지 않는 것이다.

- 파일 하나에 한 가지 일. 파일 이름은 하는 일로 짓는다.
- 주로 함수로 쓴다. 상태를 갖는 클래스는 만들지 않는다.
- common 은 다른 패키지를 import 하지 않는다 (import 검사 계약에서 가장 아래 층).
- `model` 과 `claude_utils` 는 common 을 쓰지 않는다 (계약). 그래서 이 두 곳에서 필요한 기능은 common 에 둬도 쓸 수 없다.

## 3. 대표 트리와 파일 예시

원본에 있는 세 파일이 예시다. 이 세 파일은 engine 이 쓰므로 고치지 않는다.

```
common/
├─ files.py        # 파일 접근: 원자적 쓰기, JSON·JSONL 읽기·쓰기
├─ paths.py        # 데이터 폴더 위치
└─ clock.py        # 기록에 쓰는 지금 시각
```

**files.py**: 중간에 끊겨도 반쯤 쓴 파일이 남지 않게, 임시 파일에 쓰고 이름을 바꾼다.

```python
def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=1))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
```

**paths.py**: 데이터 폴더를 한 곳에서 정한다. 시험은 환경 변수로 임시 폴더를 쓴다.

```python
def home() -> Path:
    """실행 데이터 폴더. {PKG}_HOME 이 있으면 그곳 (시험용)."""
    return Path(os.environ.get("{PKG}_HOME") or Path.cwd() / ".{pkg}")
```

**clock.py**: 기록에 쓰는 시각의 모양을 한 곳에서 정한다.

```python
def utc_now() -> str:
    """기록에 쓰는 지금 시각 (UTC, 초 단위, Z)."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
```

## 4. 구현 규칙

- 두 곳 이상에서 쓸 때만 common 에 둔다. 한 곳에서만 쓰면 그 곳(워크플로의 단계 폴더, 포트 폴더)에 둔다. **이유**: common 이 아무 기능이나 모으는 곳이 되면 무엇이 어디 있는지 찾기 어려워진다.
- 도메인 지식을 넣지 않는다. 일정, 사용자 같은 말이 함수 이름이나 본문에 나오면 common 이 아니다.
- 파일 이름과 함수 이름은 하는 일로 짓는다 (`files.py`, `write_json`). `utils.py`, `helpers.py`, `misc.py` 처럼 무엇이든 담는 이름을 쓰지 않는다.
- 설정값(폴더, 실행 파일 경로 등)은 환경 변수 `{PKG}_{이름}` 으로 바꿀 수 있게 하고, 기본값을 둔다.
- 전역 변수에 상태를 두지 않는다.
- 새 라이브러리가 필요하면 사용자에게 확인받고 `pyproject.toml` 에 더한다.

**금지**

- 이미 있는 `files.py`, `paths.py`, `clock.py` 를 고치지 않는다. engine 이 쓰고 있다. 바꿔야 하면 번들 원본을 고친다.
- 다른 패키지(`engine`, `port`, `model`, `workflow`, `claude_utils`, `entry`)를 import 하지 않는다.

## 5. 있는 것 먼저 확인

1. `src/{pkg}/common/` 을 읽고 같은 일을 하는 함수가 있는지 본다. 있으면 그것을 쓰라고 알리고 만들지 않는다.
2. 쓰는 곳이 한 곳뿐이면 common 에 두지 않고, 그 곳에 두라고 알린다.
3. 쓰는 곳이 `model` 이나 `claude_utils` 면 common 을 쓸 수 없다고 알린다.

## 6. 검증

```bash
uv run ruff check src/{pkg}/common tests/common
uv run lint-imports                 # common 이 다른 패키지를 import 하면 여기서 실패
uv run mypy
uv run pytest -q tests/common
```

새 함수마다 시험을 하나 둔다: `tests/common/test_{파일 이름}.py`.

하나라도 실패하면 고친 뒤 다시 돌린다. 통과하기 전에는 끝내지 않는다.

## 7. 산출물

- 만든 파일과 함수 목록 (함수마다 한 줄 설명)
- 그 함수를 쓸 곳
- 새로 더한 환경 변수와 의존성
