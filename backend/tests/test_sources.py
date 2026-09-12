from types import SimpleNamespace

import pytest
from medinote.schemas import SourceSegment, SourceSpan
from medinote.serialization import sha256_json
from medinote.sources import resolve_citations, validate_source_span


def test_unicode_and_unresolved():
    case = SimpleNamespace(
        segments=[SourceSegment(segment_id="s001", speaker="patient", text="Été 😀 fièvre")]
    )
    validate_source_span(case, SourceSpan(segment_id="s001", start=4, end=5, quote="😀"))
    refs = resolve_citations(case, ["s001", "absent", "s001"], "reason.001")
    assert refs[0].quote == "Été 😀 fièvre"
    assert refs[1].quote is None and not refs[1].resolvable
    assert len(refs) == 3
    assert resolve_citations(case, [], "reason.001") == []
    for start, end, quote in [(0, 1, "x"), (0, 50, "Été 😀 fièvre")]:
        with pytest.raises(ValueError):
            validate_source_span(
                case, SourceSpan(segment_id="s001", start=start, end=end, quote=quote)
            )
    with pytest.raises(ValueError):
        SourceSpan(segment_id="s001", start=-1, end=2, quote="x")


def test_hash_order():
    assert sha256_json({"b": 2, "a": "é"}) == sha256_json({"a": "é", "b": 2})
