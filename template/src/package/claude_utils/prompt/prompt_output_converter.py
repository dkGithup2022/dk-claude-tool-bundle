"""PromptOutputConverter: 출력 데이터 클래스 ↔ claude -p 의 출력 JSON.

워크플로는 프롬프트의 출력 모양을 데이터 클래스(prompt_{동작이름}_output.py)로만 쓴다.
claude -p 에 넘길 JSON 스키마를 그 클래스에서 만들고(to_schema), 받은 JSON 을 그 클래스로 바꾼다(to_data).
쓸 수 있는 필드 타입: str, int, float, bool, list[X], dict[str, X], X | None, 다른 데이터 클래스.
"""

from __future__ import annotations

import dataclasses
import types
import typing
from typing import Any


class PromptOutputConverter:
    def to_schema(self, output_type: type[Any]) -> dict[str, Any]:
        return self._schema(output_type)

    def to_data[T](self, output_type: type[T], value: Any) -> T:
        return typing.cast(T, self._data(output_type, value))

    def _schema(self, tp: Any) -> dict[str, Any]:
        if dataclasses.is_dataclass(tp):
            hints = typing.get_type_hints(tp)
            fields = [f.name for f in dataclasses.fields(tp)]
            return {"type": "object", "additionalProperties": False,
                    "properties": {name: self._schema(hints[name]) for name in fields}, "required": fields}  # fmt: skip
        origin, args = typing.get_origin(tp), typing.get_args(tp)
        if origin in (types.UnionType, typing.Union):
            inner = [a for a in args if a is not type(None)]
            if len(inner) != 1:
                raise TypeError(f"출력 필드에 쓸 수 없는 타입: {tp} (X | None 만 됨)")
            return {"anyOf": [self._schema(inner[0]), {"type": "null"}]}
        if origin is list:
            return {"type": "array", "items": self._schema(args[0])}
        if origin is dict:
            return {"type": "object", "additionalProperties": self._schema(args[1])}
        simple = {str: "string", int: "integer", float: "number", bool: "boolean"}
        if tp in simple:
            return {"type": simple[tp]}
        raise TypeError(f"출력 필드에 쓸 수 없는 타입: {tp}")

    def _data(self, tp: Any, value: Any) -> Any:
        if dataclasses.is_dataclass(tp):
            hints = typing.get_type_hints(tp)
            names = [f.name for f in dataclasses.fields(tp)]
            return tp(**{name: self._data(hints[name], value[name]) for name in names})  # type: ignore[operator]
        origin, args = typing.get_origin(tp), typing.get_args(tp)
        if origin in (types.UnionType, typing.Union):
            inner = [a for a in args if a is not type(None)][0]
            return None if value is None else self._data(inner, value)
        if origin is list:
            return [self._data(args[0], v) for v in value]
        if origin is dict:
            return {k: self._data(args[1], v) for k, v in value.items()}
        return value
