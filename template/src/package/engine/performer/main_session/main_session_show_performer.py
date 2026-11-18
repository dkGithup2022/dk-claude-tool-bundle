"""MainSessionShowPerformer: 메인 세션이 글을 보여 준다. 답을 기다리지 않는다."""

from __future__ import annotations

from package.engine.instruction.instruction_type import InstructionType
from package.engine.performer.main_session.main_session_performer import _MainSessionPerformer
from package.engine.performer.performed_by import PerformedBy


class MainSessionShowPerformer(_MainSessionPerformer):
    performed_by = PerformedBy.MAIN_SESSION_SHOW
    instruction_type = InstructionType.SHOW
