---
name: tool-assess-model
description: model 층 평가. tool-assess-port 가 요청한 도메인 데이터가 기존 model 로 충분한지 판정하고(충족 / 부분 충족 / 미충족), 최종 model 작업 계획을 세운다. 기존 클래스를 바꿔야 하면 그 자리에서 사용자에게 묻는다. 코드를 쓰지 않는다. tool-planner 가 부른다.
---

# tool-assess-model

## 0. 배경

Claude Code 에서 쓸 수 있는 로컬 도구(Python CLI + Claude 플러그인)를 만드는 스킬 모음(dk-claude-tool-bundle) 중 model 층을 평가하는 스킬이다.
model 은 워크플로와 포트가 주로 다루는 도메인 데이터(일정, 사용자 같은 것)를 불변 데이터 클래스로 두는 패키지다.
`tool-planner` 가 `tool-assess-port` 다음에 이 스킬로 "필요한 도메인 데이터가 이미 있는 model 로 되는가"를 판정한다. 데이터 스펙이 바뀌면 위 층 계획이 달라지므로, 기존 클래스를 바꿔야 하면 그 자리에서 사용자에게 묻는다.
판정 결과와 model 계획을 계획서에 적는다. 코드는 쓰지 않는다.

더 읽을 곳: `${CLAUDE_PLUGIN_ROOT}/README.md` (프로젝트 구조와 패키지 규칙), `${CLAUDE_PLUGIN_ROOT}/skills/tool-add-model/SKILL.md` (model 의 모양과 규칙).

## 1. 이 스킬의 목적

요청된 도메인 데이터를 기존 model 로 다룰 수 있는지 판정하고, model 작업 계획을 계획서에 적는다. 코드는 쓰지 않는다.

- **입력**: 계획서의 `### tool-assess-port` 절의 "model 층 요청", 계획서의 `요청` 절, `specs/models.md`
  (`specs/models.md` 가 없으면 `src/{pkg}/model/` 소스를 읽어 판단한다)
- **산출물**: 계획서의 `### tool-assess-model` 절

model 이 가장 아래 층이라 더 아래로 요청하지 않는다.

## 2. 평가 절차

### 2.1 요청마다 기존 model 을 확인한다

| 판정 | 기준 | 이어서 할 일 |
|---|---|---|
| 충족 | 같은 개념의 클래스가 있고 필드·동작도 충분함 | 없음. 있는 클래스를 적는다 |
| 부분 충족 | 클래스는 있지만 필드나 동작이 모자람 | 기존 클래스 확장 계획. **바로 사용자에게 묻는다** (2.3) |
| 미충족 | 같은 개념의 클래스가 없음 | 새 클래스 계획 |

같은 개념인지는 이름이 아니라 뜻으로 본다. 예: 요청은 `Schedule` 인데 `Todo` 가 이미 같은 것을 나타내면 `Todo` 를 쓴다.

### 2.2 계획을 세운다

새로 만들거나 바꾸는 클래스마다 정한다.

- 도메인 폴더와 파일: `model/{도메인}/{파일 이름}.py`
- 필드와 타입: 컬렉션은 `tuple`, 값이 정해져 있으면 `StrEnum`, 시각은 ISO 8601 UTC 문자열, 비어도 되면 `X | None`
- 하위 정보 클래스: 같은 뜻으로 묶이는 필드가 3개 이상이면 `{도메인}_{하위 정보}.py` 로 뺀다
- enum: 이름과 값 목록
- 값을 바꾸는 동작: 이름, 인자, 돌려주는 값(새 객체)
- `str` 과 `StrEnum` 중 애매한 필드는 "사용자 확인 필요"로 적는다

### 2.3 기존 클래스를 바꿔야 할 때

부분 충족이면 계획서를 끝까지 쓰기 전에 그 자리에서 사용자에게 묻는다. **이유**: 데이터 스펙이 바뀌면 위 층(포트) 평가가 달라진다.

묻는 내용:
- 바꾸기 전과 후 (필드 추가는 기본값과 함께 끝에)
- 그 클래스를 쓰는 곳 (`grep` 으로 찾은 포트 변환기, 워크플로)
- 이미 저장된 파일을 읽는 데 영향이 있는지

## 3. 규칙

- 코드를 쓰지 않는다. 계획만 적는다.
- model 에는 도메인 데이터만 둔다. 응답 모양 같은 스펙이면 포트의 dto 로 돌려보낸다 ("dto 로 둘 것"이라고 적는다).
- 파일·API 의 JSON 모양은 계획에 넣지 않는다 (포트 변환기의 일).
- model 은 다른 패키지를 쓰지 않는다. 지금 시각이 필요한 동작은 시각을 인자로 받게 계획한다.

## 4. 산출물

계획서의 `### tool-assess-model` 절에 아래를 적는다.

```markdown
### tool-assess-model

**판정**: 충족 / 부분 충족 / 미충족

**클래스별 계획**

- [신규] model/issue/issue.py — Issue
  - 필드: issue_id: str, title: str, opened_at: str, state: IssueState
  - 동작: close(now: str) -> Issue
- [신규] model/issue/issue_state.py — IssueState(StrEnum): OPEN = "open", CLOSED = "closed"
- [기존 확장] model/todo/todo.py — Todo
  - 바꾸기 전: (필드 목록)
  - 바꾼 뒤: (필드 목록, 더하는 필드는 기본값과 함께 끝에)
  - 영향: port/local/todo/todo_file_converter.py, workflow/...
  - 사용자 확인: 받음 / 대기

**사용자 확인 필요**

- 없음 / (항목)
```
