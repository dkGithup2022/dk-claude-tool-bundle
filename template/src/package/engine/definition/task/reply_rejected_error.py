"""build_output 이 메인 세션의 답을 받지 않을 때. 같은 지시를 다시 낸다."""

from __future__ import annotations


class ReplyRejectedError(Exception):
    """build_output 이 메인 세션의 답을 받지 않을 때. 같은 지시를 다시 낸다."""
