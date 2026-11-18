"""작업 하나. 무엇을 할지만 정하고, 상태·기록은 만지지 않는다."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from package.engine.definition.context.flow_context import FlowContext
from package.engine.definition.task.output_kind import OutputKind
from package.engine.definition.task.task_output import TaskOutput
from package.engine.request.task_request import TaskRequest


class Task(ABC):
    """작업 하나. 무엇을 할지만 정하고, 상태·기록은 만지지 않는다."""

    request_type: ClassVar[type[TaskRequest]]  # 이 작업이 만드는 요청 종류. 없으면 create 검사에서 걸림
    output_kind: ClassVar[OutputKind]  # 이 작업의 결과 종류. 없으면 create 검사에서 걸림

    @abstractmethod
    def build_request(self, context: FlowContext) -> TaskRequest:
        """수행자에게 넘길 요청을 만든다. 입력은 context 로 앞 단위의 결과에서만 읽는다."""

    @abstractmethod
    def build_output(self, context: FlowContext, result: Any) -> TaskOutput:
        """수행자가 돌려준 결과를 이 작업의 결과로 바꾼다. CODE 작업은 여기서 일을 한다.

        FILES 작업은 파일을 직접 쓰지 않고 TaskOutput.files 로 돌려준다. 서브에이전트가 쓴 파일은 engine 이 모은다.
        """
