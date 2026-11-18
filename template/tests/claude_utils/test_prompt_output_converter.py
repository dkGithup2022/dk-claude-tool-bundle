from __future__ import annotations

from dataclasses import dataclass

import pytest

from package.claude_utils.prompt.prompt_output_converter import PromptOutputConverter


@dataclass(frozen=True, slots=True)
class Season:
    fruit: str
    months: list[int]


@dataclass(frozen=True, slots=True)
class SeasonsOutput:
    seasons: list[Season]
    note: str | None
    scores: dict[str, float]


def test_should_make_schema_with_every_field_required_and_no_extra_fields():
    schema = PromptOutputConverter().to_schema(SeasonsOutput)
    assert schema["required"] == ["seasons", "note", "scores"] and schema["additionalProperties"] is False
    season = schema["properties"]["seasons"]["items"]
    assert season["properties"]["months"] == {"type": "array", "items": {"type": "integer"}}
    assert schema["properties"]["note"] == {"anyOf": [{"type": "string"}, {"type": "null"}]}
    assert schema["properties"]["scores"] == {"type": "object", "additionalProperties": {"type": "number"}}


def test_should_turn_output_json_into_dataclass():
    out = PromptOutputConverter().to_data(
        SeasonsOutput, {"seasons": [{"fruit": "배", "months": [9, 10]}], "note": None, "scores": {"배": 0.5}}
    )
    assert out == SeasonsOutput([Season("배", [9, 10])], None, {"배": 0.5})


def test_should_refuse_unsupported_field_type():
    @dataclass
    class Bad:
        when: set[str]

    with pytest.raises(TypeError, match="쓸 수 없는 타입"):
        PromptOutputConverter().to_schema(Bad)
