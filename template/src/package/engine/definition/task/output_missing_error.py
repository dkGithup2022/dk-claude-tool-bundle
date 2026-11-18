"""읽으려는 노드의 결과가 없음 (건너뛴 노드 등, )."""

from __future__ import annotations


class OutputMissingError(LookupError):
    """읽으려는 노드의 결과가 없음 (건너뛴 노드 등, )."""
