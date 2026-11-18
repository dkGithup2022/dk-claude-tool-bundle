"""작업 결과의 종류. Task 마다 선언하고, 앞 결과를 읽는 쪽은 이것을 보고 읽는 방법을 고른다."""

from __future__ import annotations

from enum import StrEnum


class OutputKind(StrEnum):
    """작업 결과의 종류. Task 마다 선언하고, 앞 결과를 읽는 쪽은 이것을 보고 읽는 방법을 고른다."""

    DATA = "data"  # dict. <노드 폴더>/result.json 에 저장
    FILES = "files"  # 텍스트 파일(md, txt, 코드). 산출물 폴더에 생긴 파일 전부가 결과
