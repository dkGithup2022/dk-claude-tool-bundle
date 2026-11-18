---
name: run
description: package 흐름을 실행한다. 순서와 상태는 package 명령이 정하고, 이 세션은 명령이 시키는 한 가지만 한다
disable-model-invocation: true
argument-hint: <흐름 이름>
---
흐름 `$ARGUMENTS` 를 실행합니다. 순서, 상태, 데이터는 `package` 명령이 정합니다. 이 세션은 명령이 돌려준 지시 하나만 처리하고, 다른 판단이나 파일 쓰기를 하지 않습니다.

1. `$ARGUMENTS` 의 첫 단어(흐름 이름)만 넘겨 `package start <흐름 이름>` 을 Bash 로 부릅니다. 나머지 글은 넘기지 않습니다(대화 기록에 그대로 남아 단계가 읽습니다).
2. 결과 JSON 은 지시 하나입니다: `{"type", "node_uuid", "item_key", "payload"}`. `type` 대로 한 가지만 합니다. 내용은 `payload` 안에 있습니다.
   - `show`: `payload.text` 의 내용을 사용자에게 답변으로 알리고 `package next` 를 부릅니다. 명령의 결과(JSON)는 사용자에게 보이지 않으므로, 답변에 옮기지 않으면 사용자는 그 내용을 보지 못합니다.
   - `ask`: AskUserQuestion 으로 `payload.question` 과 `payload.choices` 를 그대로 묻습니다. 사용자의 답(고른 라벨 또는 직접 입력한 글)을 바꾸지 않고 `package done --answer "<답>"` 으로 넘깁니다.
   - `talk`: `payload.opening` 으로 대화를 시작해 `payload.goal` 을 향해 사용자와 이야기합니다. 충분하면 AskUserQuestion 으로 "정리할까요?" (예 / 더 이야기) 를 묻고, 예면 `package done` 을 부릅니다.
   - `spawn`: Agent 도구로 `payload.agent` 를 `payload.message` 그대로 띄웁니다. 백그라운드로 시작되면 완료 알림이 올 때까지 기다립니다. 서브에이전트가 끝난 뒤에 `package done` 을 부릅니다. 파일이 생긴 것만 보고 부르지 않습니다.
   - `finished`: `payload.text` 를 보이고 끝냅니다.
   - `failed`: `payload.text` 를 보이고 멈춥니다. 사용자가 다시 하자고 하면 `package next` 를 부릅니다.
3. `done` 의 결과도 다음 지시입니다. 2 를 반복합니다.
