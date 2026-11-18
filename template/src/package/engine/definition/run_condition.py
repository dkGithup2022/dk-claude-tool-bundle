"""RunCondition: 조건 함수의 모양."""

from __future__ import annotations

from collections.abc import Callable

from package.engine.definition.context.flow_context import FlowContext

RunCondition = Callable[[FlowContext], bool]  # 앞 단위의 결과로만 판단. CONDITIONS 가 만든다
