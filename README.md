# dk-claude-tool-bundle

Claude 와 연동해서 사용할 수 있는 도구를 만드는 데 집중합니다.
Python 과 Claude 플러그인, 스킬을 이용해 기능을 제공합니다.

특히 다음 두 가지에 구조를 제공합니다.

- 프롬프트 호출이나 Python 코드 호출을 연달아 수행하는 워크플로
- 워크플로에서 이전 작업 결과를 참조해야 하는 복잡한 작업

이 내용은 `engine` 과 `workflow` 패키지에서 다룹니다.

## 설치

필요한 것: Claude Code, [uv](https://docs.astral.sh/uv/), Python 3.12 이상.

```text
/plugin install dk-claude-tool-bundle --marketplace dkGithup2022/dk-claude-tool-bundle
```

Claude Code 2.1.275 보다 앞선 버전에서는 두 단계로 설치합니다.

```text
/plugin marketplace add dkGithup2022/dk-claude-tool-bundle
/plugin install dk-claude-tool-bundle@dk-claude-tool-bundle
```

설치한 뒤 빈 폴더에서 새 프로젝트를 만들고, 그 위에 기능을 더합니다.

```text
/dk-claude-tool-bundle:tool-init                 # 새 프로젝트 (빈 폴더에서 한 번)
/dk-claude-tool-bundle:tool-workflow-planner     # 워크플로 더하기
/dk-claude-tool-bundle:tool-planner              # 워크플로가 아닌 기능(바깥 API, 로컬 데이터, 도메인 데이터) 더하기
```

스킬은 대부분 초안입니다 (아래 스킬 표의 상태).

## 코드 퀄리티의 기준

### 파악이 쉽다
- 정해진 위치에 정해진 소스가 있다.
- 클래스 하나에 파일 하나를 둔다. 자바 스타일로 개발한다는 생각으로 쓴다.
- 묶이는 것은 폴더로 묶는다. 한 폴더 아래에 계층 없이 모두 나열하지 않는다.

### 테스트할 수 있다
- 바깥 데이터는 포트를 거쳐서만 다룬다.

## 프로젝트 구조

초기화 스킬이 만드는 프로젝트의 모양입니다. 원본은 이 레포의 `template/` 에 있고, 패키지 이름은 `package` 입니다.

```
{project}/
├─ src/{pkg}/
│  ├─ entry/          명령 진입점
│  ├─ engine/         실행에 필요한 공용 기능 (실행 틀)
│  ├─ workflow/       기능 단위 구현
│  ├─ model/          도메인 데이터
│  ├─ port/           바깥 데이터를 다루는 인터페이스와 구현
│  ├─ claude_utils/   Claude 관련 기능
│  └─ common/         공용 파일 쓰기, 경로 계산
├─ plugin/            Claude 플러그인 (plugin.json, bin, hooks, skills, agents)
└─ tests/
```

## 패키지별 규칙

### entry
명령 진입점입니다. 인자 해석과 실행기 조립만 합니다.

### engine
실행에 필요한 공용 기능입니다. 기능 구현은 여기에 넣지 않습니다.
초기화 스킬이 새 프로젝트를 만들 때 engine 코드를 프로젝트에 복사합니다. 프로젝트마다 engine 코드를 가집니다.
안쪽 구조와 규칙은 [docs/engine.md](docs/engine.md) 에 따로 둡니다.

### workflow
기능 구현은 이 폴더에서 합니다. 기능마다 폴더 하나를 둡니다.
폴더 모양, 이름, 단계의 결과 종류와 앞 결과 읽기 같은 제작 규칙은 [docs/workflow.md](docs/workflow.md) 에 따로 둡니다.

### model
주요하게 다뤄야 하는 데이터, 즉 도메인 데이터로서 다루는 것을 둡니다. 예를 들면 user, history, state 입니다.

- 하위에 계층 없이 모든 정보를 나열하지 않습니다. 묶이는 정보는 폴더로 묶습니다.
- 클래스 하나에 파일 하나를 둡니다.
- 불변으로 만듭니다.

```
model/
└─ user/
   ├─ user.py
   └─ user_auth_info.py      user 아래의 oauth 정보
```

### port
바깥 데이터를 다루는 인터페이스를 둡니다. 바깥 API 를 부르는 것, model 을 파일로 넣고 읽는 것이 여기에 들어갑니다.

- 다른 포트는 다른 폴더에 둡니다. 로컬 파일을 다루는 포트는 `local/` 아래에 모읍니다.
- 포트 인터페이스, 포트 구현체, 포트 인터페이스가 주고받는 스펙(dto)은 각각 별도 파일로 둡니다.
- 구현체 이름은 `default_` 로 시작합니다.
- 읽기만 하는 포트는 Reader 만 둡니다. 쓰기가 있으면 Writer 를 더합니다.
- dto 에는 주체가 되지는 않지만 스펙으로 가지고 있어야 하는 것을 둡니다. API 의 스펙이나 그 스펙에 포함된 정보, join 의 결과물 같은 것입니다. 그래서 포트 아래에 둡니다.

```
port/
├─ gh/                          읽기만 하는 포트
│  ├─ gh_reader.py              인터페이스
│  ├─ default_gh_reader.py      구현체
│  └─ dto/
│     ├─ gh_login_info.py
│     └─ gh_token_info.py
└─ local/
   ├─ history/                  읽기와 쓰기가 있는 포트
   │  ├─ history_reader.py
   │  ├─ history_writer.py
   │  ├─ default_history_reader.py
   │  ├─ default_history_writer.py
   │  └─ dto/
   └─ run_state/
      └─ ...
```

### claude_utils
Claude 관련 기능을 둡니다. 대화 기록에서 대화를 뽑는 기능과 프롬프트 실행(claude -p)이 여기에 들어갑니다. 주요 기능, 역할 단위로 폴더를 둡니다.

```
claude_utils/
├─ transcript/     대화 기록에서 대화 뽑기
└─ prompt/         claude -p 실행
```

### common
engine 과 port 가 같이 쓰는 코드를 둡니다. 원자적 파일 쓰기, JSON 읽기·쓰기, JSONL 덧붙이기, 데이터 폴더(`.{pkg}/`, 환경 변수 `{PKG}_HOME`) 경로 계산입니다.

## 의존 방향

```
entry ──→ workflow ──→ engine ──→ claude_utils
   │         ├──→ port ──→ model
   │         ├──→ model
   │         └──→ claude_utils
   └──→ (모든 패키지: 조립만)

engine, port ──→ common
```

| 패키지 | import 해도 되는 것 |
|---|---|
| model | 없음 |
| common | 없음 |
| port | model, common |
| claude_utils | 없음 (프로젝트 코드를 모름) |
| engine | claude_utils, common |
| workflow | engine, model, port (인터페이스와 구현체 모두), claude_utils |
| entry | 전부. 조립하는 곳 |

이 규칙은 지금은 소스를 파악하기 쉽게 하는 역할만 합니다. 그래서 workflow 가 port 의 구현체(`default_...`)를 직접 import 하는 것을 허용합니다.

## 공통 규칙

- 파일 이름은 파이썬 관례대로 소문자와 밑줄로 씁니다(`gh_reader.py`). 클래스 이름은 `GhReader` 처럼 씁니다.
- 클래스 하나에 파일 하나를 둡니다.

## 스킬

| 스킬 | 하는 일 | 상태 |
|---|---|---|
| `tool-init` | 새 프로젝트 만들기: `template/` 복사, 이름 바꾸기, 검증 | 있음 |
| `tool-add-model` | `model/` 에 도메인 데이터 클래스 | 초안 |
| `tool-add-port` | `port/` 에 로컬 파일·바깥 API 포트 | 초안 |
| `tool-add-common` | `common/` 에 공통 기능 | 초안 |
| `tool-workflow-planner` | 워크플로 제작의 진입점: 계획서 확답 → 단계 제작 스킬 호출 → 선언·`FLOWS` 등록 → 끝까지 시험 | 초안 |
| `tool-workflow-planner-extract-plan` | 대화로 워크플로 계획서(흐름도, 단계별 상세)를 채움. 항목별 값과 enum, 추론 규칙, 대화 순서, 케이스별 예시 | 초안 |
| `tool-add-session-task` | 워크플로 단계: 보이기·묻기·대화 | 초안 |
| `tool-add-code-task` | 워크플로 단계: 코드 | 초안 |
| `tool-add-prompt-task` | 워크플로 단계: 프롬프트 (`prompt_{동작이름}.md`, 출력 데이터 클래스) | 초안 |
| `tool-add-subagent-task` | 워크플로 단계: 서브에이전트 (에이전트 정의, 산출물 폴더를 알리는 메시지) | 초안 |
| `tool-planner` | 워크플로가 아닌 일(바깥 API 연동, 유틸 기능, 모델·포트): 평가 → 계획서 확인 → 제작 | 초안 |
| `tool-assess-port` | 필요한 바깥 데이터 접근이 기존 포트로 되는지 판정, 포트 계획 | 초안 |
| `tool-assess-model` | 필요한 도메인 데이터가 기존 model 로 되는지 판정, model 계획 | 초안 |

```text
/dk-claude-tool-bundle:tool-init        # 빈 폴더에서 한 번
```

## 아직 정하지 않은 것

- DI 도구를 채용할지
- 스킬 목록 중 예정인 것들 (초안은 `docs/workflow.md` 5.4 절)
