"""ItemsSource: 반복 항목 함수의 모양."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from package.engine.definition.context.flow_context import FlowContext

ItemsSource = Callable[[FlowContext], list[Any]]  # 반복할 항목. ITEM_SOURCES 가 만든다
