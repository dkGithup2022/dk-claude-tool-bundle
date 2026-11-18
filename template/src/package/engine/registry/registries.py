"""레지스트리 셋: 작업, 조건, 반복 항목."""

from __future__ import annotations

from package.engine.definition.items_source import ItemsSource
from package.engine.definition.run_condition import RunCondition
from package.engine.definition.task.task import Task
from package.engine.registry.in_memory_registry import InMemoryRegistry
from package.engine.registry.registry import Registry

TASKS: Registry[Task] = InMemoryRegistry("작업")


CONDITIONS: Registry[RunCondition] = InMemoryRegistry("조건")


ITEM_SOURCES: Registry[ItemsSource] = InMemoryRegistry("반복 항목")
