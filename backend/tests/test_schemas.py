import pytest
from medinote.schemas import DirectAssertion, ExtractedFact, Subject
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError


def test_nullable_strict():
    schema = to_strict_json_schema(ExtractedFact)
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["additionalProperties"] is False
    with pytest.raises(ValidationError):
        Subject(kind="patient")
    with pytest.raises(ValidationError):
        Subject(kind="relative", label=None)


def test_additional_and_limits():
    with pytest.raises(ValidationError):
        DirectAssertion(text="a", source_ids=[], extra="no")
    with pytest.raises(ValidationError):
        DirectAssertion(text="a" * 1001, source_ids=[])
    with pytest.raises(ValidationError):
        DirectAssertion(text="a", source_ids=["s001"] * 9)
