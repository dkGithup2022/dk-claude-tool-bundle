"""demo 워크플로 선언.

폴더는 아래 선언의 단위 트리와 같은 모양이다. 각 폴더의 Task·반복 항목 함수를 import 해 등록한다.
"""

from __future__ import annotations

from package.engine.builtin import answer_is  # noqa: F401  (조건 answer_is 등록)
from package.engine.definition.flow_definition import FlowDefinition
from package.engine.definition.ref import Ref
from package.engine.definition.unit.builders import group, task
from package.engine.performer.performed_by import PerformedBy
from package.engine.runner.child_run.child_run import ChildRun
from package.workflow.demo.bye import bye_task  # noqa: F401
from package.workflow.demo.check.ask_check import ask_check_task  # noqa: F401
from package.workflow.demo.check.confirm_each import fruits_items  # noqa: F401
from package.workflow.demo.check.confirm_each.confirm import confirm_task  # noqa: F401
from package.workflow.demo.hello import hello_task  # noqa: F401
from package.workflow.demo.talk.collect_fruits import collect_fruits_task  # noqa: F401
from package.workflow.demo.talk.listen import listen_task  # noqa: F401

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
)  # fmt: skip
