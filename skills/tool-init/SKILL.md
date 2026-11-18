---
name: tool-init
description: Claude 와 연동해서 쓰는 로컬 도구 프로젝트를 새로 만든다. 번들의 template/ 을 복사하고 이름(package, PACKAGE_)을 프로젝트 이름으로 바꾼 뒤, 실행 틀(engine)·Claude 유틸·CLI·플러그인 뼈대·시험 기반과 예시 워크플로 2개(demo, count_joke)가 그대로 도는지 검증한다. 워크플로·모델·포트는 만들지 않는다. 이미 프로젝트가 있는 폴더(pyproject.toml, src/, plugin/ 중 하나라도 있음)에서는 시작하지 않는다.
---

# tool-init

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 새 프로젝트를 만드는 스킬이다. 다른 모든 스킬은 이 스킬이 만든 프로젝트 위에서 일한다.
만든 프로젝트는 워크플로 실행 엔진(engine)을 가진 Python CLI 와, 그 CLI 를 부르는 Claude 플러그인이다. 사용자는 Claude Code 에서 `/{pkg}:run <워크플로>` 로 워크플로를 실행하고, Claude 세션은 CLI 가 돌려준 지시를 하나씩 처리한다.
엔진과 기반 코드는 번들의 `template/` 에 시험을 통과한 상태로 있고, 이 스킬은 그것을 복사해 이름만 바꾼다. 그래서 복사한 코드를 고치지 않는다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/docs/engine.md`.

새 프로젝트를 만든다. 한 프로젝트에 한 번만 실행한다.

## 1. 스킬 경계

**만드는 것**: `template/` 의 전부. 구조와 파일마다의 역할은 `${CLAUDE_PLUGIN_ROOT}/docs/engine.md` 5.1 절에 있다.

| 무엇 | 위치 |
|---|---|
| 실행 틀 | `src/{pkg}/engine/` |
| Claude 유틸 (claude -p 호출, 대화 기록 읽기) | `src/{pkg}/claude_utils/` |
| 공용 코드 (파일 쓰기, 데이터 폴더, 시각) | `src/{pkg}/common/` |
| CLI 진입점 | `src/{pkg}/entry/cli.py`, `src/{pkg}/__main__.py` |
| 워크플로 목록과 예시 워크플로 | `src/{pkg}/workflow/registry.py`, `workflow/demo/`, `workflow/count_joke/` |
| 예시가 쓰는 모델과 포트 | `src/{pkg}/model/counter/`, `src/{pkg}/port/local/counter/` |
| Claude 플러그인 | `plugin/` (`plugin.json`, `bin/{pkg}`, 훅, `run` 스킬, `agents/`) |
| 시험 | `tests/` (engine, claude_utils, model, port, workflow, CLI) |
| 설정 | `pyproject.toml` (ruff, mypy strict, pytest, import 검사 계약 4개) |
| 코드 따라가기 도구 | `scripts/trace_calls.py` |

**만들지 않는 것**

- 새 워크플로, 모델, 포트. 워크플로는 워크플로 제작 스킬이, 모델·포트·바깥 API 연동·유틸 기능은 planner 가 만든다.
- git 저장소, 원격 저장소, CI.
- 예시 워크플로(demo, count_joke)를 지우는 일. 시험이 예시에 기대고 있고, 다른 스킬이 예시를 레퍼런스로 쓴다.

## 2. 입력

| 입력 | 뜻 | 규칙 |
|---|---|---|
| 프로젝트 폴더 | 만들 위치 | 비어 있거나 없는 폴더. `pyproject.toml`, `src/`, `plugin/` 중 하나라도 있으면 시작하지 않는다 |
| `{pkg}` | 프로젝트 이름. 파이썬 패키지, CLI 명령, 플러그인 이름, 데이터 폴더(`.{pkg}/`), 환경 변수 접두어(`{PKG}_`)에 같이 쓰인다 | 영문 소문자로 시작, 영문 소문자·숫자·`_` 만. 파이썬 예약어·표준 라이브러리 이름(`json`, `test` 등)은 안 됨 |

사용자가 주지 않은 입력은 묻는다. 프로젝트 폴더의 기본값은 지금 작업 폴더, `{pkg}` 의 기본값은 폴더 이름을 위 규칙에 맞게 바꾼 것(`my-tool` → `my_tool`)으로 제안한다.

## 3. 실행 순서

1. **도구 확인**: `uv --version`. 없으면 6 절의 대응을 안내하고 멈춘다.
2. **복사와 이름 바꾸기**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/tool-init/scripts/init_project.py --target <프로젝트 폴더> --pkg <pkg>
   ```
   출력 JSON 의 `ok` 가 `false` 면 `error` 를 사용자에게 보이고 멈춘다. 입력을 고쳐 다시 받는다.
   스크립트가 하는 일:
   - `template/` 을 복사한다 (`.venv`, 캐시, `uv.lock` 제외).
   - `src/package/` → `src/{pkg}/`, `plugin/bin/package` → `plugin/bin/{pkg}` 로 이름을 바꾼다.
   - 모든 텍스트 파일에서 낱말 `package` → `{pkg}`, `PACKAGE_` → `{PKG}_` 로 바꾼다. `pyproject.toml` 의 `[tool.uv] package = true` 는 uv 설정 키라 그대로 둔다.
3. **환경 만들기와 정리**: 프로젝트 폴더에서
   ```bash
   uv sync
   uv run ruff check --fix --select I .     # 이름이 길어져 넘친 import 줄을 감싼다
   uv run ruff format .
   ```
4. **검증**: 5 절. 실패하면 6 절.
5. **보고**: 7 절.

## 4. 바꾸지 않는 것

이 스킬은 복사한 코드를 고치지 않는다. 원본은 번들에서 시험을 통과한 상태이므로, 검증이 실패하면 원인은 대개 환경이다.
코드가 원인으로 보이면 고치지 말고 6 절대로 멈추고 알린다. 원본을 고치는 일은 번들 레포에서 한다.

## 5. 검증

프로젝트 폴더에서 차례로 실행한다. 하나라도 실패하면 다음으로 가지 않는다.

```bash
uv run ruff check .                 # 문법과 스타일
uv run lint-imports                 # 패키지 사이 의존 방향 (계약 4개)
uv run mypy                         # 타입 (strict)
uv run pytest -q                    # 시험 전부
{PKG}_HOME=$(mktemp -d) plugin/bin/{pkg} --session init-check start demo
```

마지막 명령은 실제 CLI 로 demo 워크플로를 시작한다. 출력 JSON 의 `type` 이 `show` 이고 `payload.text` 가 `"가짜 흐름을 시작합니다."` 이면 통과다.

## 6. 실패 모드

| 증상 | 원인 | 대응 |
|---|---|---|
| `uv: command not found` | uv 없음 | `brew install uv` 또는 `curl -LsSf https://astral.sh/uv/install.sh \| sh` 를 안내하고 멈춤 |
| `No interpreter found` | 맞는 Python 없음 | `uv python install 3.13` 실행 후 3 단계부터 다시 |
| `No solution found` (uv sync) | 의존성 받기 실패 | 네트워크·프록시를 확인하라고 알리고 멈춤. 파일은 그대로 둠 |
| `init_project.py` 의 `ok: false` | 이름 규칙 위반, 이름이 30자를 넘음, 이미 프로젝트가 있는 폴더 | `error` 를 보이고 입력을 다시 받음 |
| `E501 Line too long` | 3 단계의 정리를 건너뜀 | 3 단계를 다시 한 뒤 검증 |
| 그 밖의 검증 실패 | 원본 또는 복사 결과 문제 | 고치지 않는다. 실패한 명령과 출력 전체를 보이고 멈춤. 만든 파일은 지우지 않는다 |

같은 단계를 세 번 다시 해도 실패하면 멈추고 알린다.

## 7. 완료 보고

아래를 사용자에게 보인다.

- 만든 위치와 `{pkg}`
- 검증 결과: ruff, lint-imports(계약 4개), mypy, pytest(통과 수), CLI 시작 결과
- 써 보는 방법:
  ```bash
  cd <프로젝트 폴더>
  claude --plugin-dir <프로젝트 폴더>/plugin      # 플러그인을 올려 Claude Code 실행
  /{pkg}:run demo                                 # Claude Code 안에서
  /{pkg}:run count_joke
  ```
- 다음에 쓸 스킬: 워크플로는 워크플로 제작 스킬(대화형), 모델·포트·바깥 API 연동·유틸 기능은 planner
- 읽을 문서: 번들의 `README.md`(구조와 패키지 규칙), `docs/engine.md`, `docs/workflow.md`

## 8. 이후 스킬이 지킬 규약

이 스킬이 만든 기반 위에서 다른 스킬이 지키는 약속이다. 자세한 내용은 번들의 `README.md` 와 `docs/` 에 있다.

| 주제 | 약속 |
|---|---|
| 고치지 않는 것 | `engine/`, `claude_utils/`, `entry/` 와, `common/` 에 처음부터 있는 파일(`files.py`, `paths.py`, `clock.py`)은 고치지 않는다. 필요하면 번들 원본을 고친다. `common/` 에 새 파일을 더하는 것은 `tool-add-common` 이 한다 |
| 이름 | 파이썬 패키지 `{pkg}`, 데이터 폴더 `.{pkg}/`, 환경 변수 `{PKG}_HOME`(데이터 폴더), `{PKG}_CLAUDE_BIN`(claude 실행 파일) |
| 의존 방향 | `pyproject.toml` 의 import 검사 계약 4개를 바꾸지 않는다. 새 코드는 계약 안에서 쓴다 |
| 워크플로 | `workflow/<이름>/` 에 만들고, 선언은 `<이름>_flow.py`, 등록은 `workflow/registry.py` 의 `FLOWS`. 규칙은 `docs/workflow.md` |
| 모델과 포트 | 도메인 데이터는 `model/`, 바깥 API·파일은 `port/`. 규칙은 `README.md` 의 패키지별 규칙 |
| 의존성 추가 | `pyproject.toml` 의 `dependencies` 에 더하기 전에 사용자에게 확인한다 |
| 예시 | `workflow/demo/`, `workflow/count_joke/`, `model/counter/`, `port/local/counter/` 는 시험과 레퍼런스가 기대고 있다. 지우려면 그 시험도 함께 지운다 |
