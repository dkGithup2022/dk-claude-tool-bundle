---
name: tool-planner
description: 워크플로가 아닌 기능 요청(바깥 API 연동, 로컬 데이터 저장, 도메인 데이터, 공통 기능)을 받아 평가 스킬(tool-assess-port → tool-assess-model)을 위에서 아래로 실행하고, 계획서를 써서 사용자 확인을 받은 뒤, 제작 스킬(tool-add-model → tool-add-port → tool-add-common)을 아래에서 위로 실행한다. 워크플로 요청은 받지 않고 워크플로 제작 스킬로 넘긴다.
---

# tool-planner

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 워크플로가 아닌 기능을 계획하고 만드는 스킬이다.
프로젝트는 entry(CLI 진입점), engine(워크플로 실행 엔진), workflow(기능 구현), model(도메인 데이터), port(바깥 데이터 접근), claude_utils(Claude 관련 기능), common(공통 기능)으로 나뉜다.
워크플로는 `tool-workflow-planner` 가 대화로 만들고, 그 밖의 기능(바깥 API 연동, 로컬 데이터 저장, 도메인 데이터, 공통 기능)은 이 스킬이 맡는다. 이 기능들은 대개 워크플로의 단계가 가져다 쓴다.
이 스킬은 요청을 층별로 평가하고(`tool-assess-port` → `tool-assess-model`), 계획서를 사용자에게 확인받은 뒤, 제작 스킬(`tool-add-model` → `tool-add-port` → `tool-add-common`)을 부른다. 층마다 스킬을 나눈 것은 스킬 하나가 다루는 범위를 좁혀 결과물을 정해진 모양으로 만들기 위해서다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md` 5.4 절(스킬 나누기).

## 1. 이 스킬의 목적

기능 요청 하나를 받아 평가 → 계획서 → 사용자 확인 → 제작까지 진행한다. 각 단계는 해당 스킬을 불러서 하고, 결과는 계획서 한 파일에 쌓는다.

- **받는 요청**: 바깥 API 연동(예: GitHub 이슈 읽기), 로컬 데이터 저장(예: 설정을 파일로), 도메인 데이터(예: 사용자 정보), 여러 곳이 같이 쓰는 공통 기능
- **받지 않는 요청**: 워크플로(순서대로 여러 단계를 실행하고, 사용자에게 묻고, 프롬프트를 부르고, 반복하는 일). 워크플로 제작 스킬로 넘긴다. 요청에 둘이 섞여 있으면 워크플로가 쓸 포트·model 만 여기서 만들고, 워크플로 부분은 넘긴다고 알린다.

## 2. 사전 조건

- `tool-init` 으로 만든 프로젝트다: `pyproject.toml` 과 `src/{pkg}/engine/` 이 있다. 없으면 `tool-init` 을 먼저 안내하고 멈춘다.
- `{pkg}` 는 `src/` 아래에 있는 유일한 폴더 이름이다.

## 3. 부르는 스킬

| 줄임 이름 | 스킬 ID | 하는 일 |
|---|---|---|
| assess-port | `dk-claude-tool-bundle:tool-assess-port` | 필요한 바깥 데이터 접근이 기존 포트로 되는지, 포트 계획, model 층 요청 |
| assess-model | `dk-claude-tool-bundle:tool-assess-model` | 필요한 도메인 데이터가 기존 model 로 되는지, model 계획 |
| add-model | `dk-claude-tool-bundle:tool-add-model` | model 만들기·바꾸기 |
| add-port | `dk-claude-tool-bundle:tool-add-port` | 포트 만들기·바꾸기 |
| add-common | `dk-claude-tool-bundle:tool-add-common` | 공통 기능 더하기 |

## 4. 계획서

평가 결과와 계획, 진행 기록을 한 파일에 쌓는다. 다음 스킬은 이 파일을 읽고 앞 결과를 쓴다.

- 경로: `specs/plans/{요청 이름}.md`. 요청 이름은 하는 일을 영문 소문자와 `-` 로 (예: `read-github-issues`). `specs/plans/` 가 없으면 만든다.

```markdown
# 계획: {요청 한 줄}

## 요청
{사용자가 말한 그대로}

## 1. 평가

### 나누기
- 포트: {바깥 데이터 접근 목록}
- 공통 기능: {있으면}
- 워크플로로 넘길 것: {있으면}

### tool-assess-port
### tool-assess-model

## 2. 구현 계획
{평가 요약, 정한 것, 구현 순서}

## 3. 진행 기록
{제작 스킬마다 결과와 검증 출력 요약}
```

## 5. 1 단계: 평가 (위에서 아래로)

1. **요청 나누기**: 요청을 아래로 나눠 계획서 `### 나누기` 에 적는다.
   - 포트: 바깥 데이터를 읽고 쓰는 일 (API, 파일)
   - 공통 기능: 두 곳 이상이 같이 쓰고 도메인 지식이 없는 기능 (로깅, 파일 접근 같은 것). 한 곳에서만 쓰면 공통 기능이 아니라 그 곳에 둔다
   - 워크플로로 넘길 것
   - 요청이 모호해서 나눌 수 없으면 사용자에게 묻는다. 무엇을 읽고 쓰는지, 어디서(API·파일), 결과를 어디에 쓰는지.
2. **assess-port** 를 부른다. 결과를 `### tool-assess-port` 에 적는다.
   - 충족이고 model 층 요청이 없으면 3 으로 가지 않는다.
3. **assess-model** 을 부른다. 결과를 `### tool-assess-model` 에 적는다.

**바로 묻는 경우**: 평가 중 아래가 나오면 2 단계까지 미루지 않고 그 자리에서 사용자에게 묻는다. 데이터 스펙이 바뀌면 다른 평가가 달라지기 때문이다.
- 기존 model 클래스를 바꿔야 함
- 기존 포트의 메서드나 파일 저장 모양을 바꿔야 함
- 새 라이브러리가 필요함

## 6. 2 단계: 계획을 보이고 확인받기

평가를 모아 계획서 `## 2. 구현 계획` 에 적고, 사용자에게 보인다.

```
[요청]: GitHub 저장소의 열린 이슈를 읽어 온다

[평가]
- port: 미충족 — port/gh/ 신규, GhReader.list_issues
- model: 충족 — 이슈는 GhIssue dto 로 충분 (도메인 데이터 아님)
- 공통 기능: 없음

[정한 것]
- 호출: gh CLI, 새 의존성 없음, 환경 변수 {PKG}_GH_BIN
- 실패: GhApiError

[구현 순서]
1. add-port: port/gh/ (GhReader, DefaultGhReader, GhApiConverter, GhApiError, dto/gh_issue.py), 시험, specs/ports.md
```

사용자가 고치면 계획서를 고치고 다시 보인다. 확인을 받은 뒤에 3 단계로 간다.

## 7. 3 단계: 제작 (아래에서 위로)

확인받은 계획서대로, 미충족·부분 충족인 것만 아래 순서로 부른다. 동시에 부르지 않는다.

```
add-model → add-port → add-common
```

- 각 스킬은 계획서의 자기 층 계획을 읽고 작업한다.
- 각 스킬이 끝나면 결과와 검증 출력 요약을 `## 3. 진행 기록` 에 적는다.
- 스킬의 검증이 통과하지 않으면 다음 스킬로 가지 않는다. 그 스킬 안에서 고친 뒤 다시 검증한다. 세 번 다시 해도 실패하면 멈추고 사용자에게 알린다.
- 계획과 다르게 만들어야 할 일이 생기면 멈추고 사용자에게 묻는다.

## 8. 최종 검증

모든 제작이 끝나면 프로젝트 전체를 검증한다.

```bash
uv run ruff check .
uv run lint-imports
uv run mypy
uv run pytest -q
```

## 9. 완료 보고

- 만든·바꾼 파일 목록 (층별)
- 갱신한 스펙 문서 (`specs/models.md`, `specs/ports.md`)
- 새 환경 변수, 새 의존성
- 최종 검증 결과
- 워크플로로 넘긴 것이 있으면, 이번에 만든 포트·model 을 그 워크플로에서 어떻게 쓰면 되는지 한 줄씩

## 10. 경우별 실행 범위

```
경우 A: 새 바깥 API 를 읽기만 함, 응답은 dto 로 충분
  평가: assess-port (미충족) → assess-model (요청 없음, 건너뜀)
  제작: add-port

경우 B: 새 도메인 데이터를 파일에 저장
  평가: assess-port (미충족) → assess-model (미충족)
  제작: add-model → add-port

경우 C: 기존 포트에 메서드 하나 추가
  평가: assess-port (부분 충족) → (model 요청 없으면 끝)
  제작: add-port

경우 D: 공통 기능만
  평가: 나누기에서 공통 기능 확인 (포트·model 평가 없음)
  제작: add-common
```
