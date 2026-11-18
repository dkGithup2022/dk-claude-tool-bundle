"""흐름에 상관없이 쓰는 조건. import 될 때 등록된다."""

from __future__ import annotations

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.run_condition import RunCondition
from package.engine.definition.task.output_missing_error import OutputMissingError
from package.engine.registry.registries import CONDITIONS


@CONDITIONS.register_as("answer_is")
def answer_is(node_name: str, value: str) -> RunCondition:
    """앞 노드의 답(data["answer"])이 value 인가. 그 노드를 건너뛰었으면 거짓.

    조건을 단 단위의 reads 에 node_name 을 적는다.
    """

    def check(context: FlowContext) -> bool:
        try:
            return bool(context.read(node_name).get("answer") == value)
        except OutputMissingError:
            return False

    return check
