import pytest
from evaluation_helpers import annotated_example
from medinote.evaluation.alignment import validate_alignment, validate_annotation_completeness
from medinote.serialization import sha256_file


def test_alignment_and_multifacts(root):
    case, gold, note, a = annotated_example(root)
    assert validate_alignment(
        a, note, gold, case, sha256_file(root / "eval/annotation-guide.v1.md")
    )
    validate_annotation_completeness(a)
    a.claims[0].spans[0].quote = "faux"
    with pytest.raises(ValueError, match="Span"):
        validate_alignment(a, note, gold, case, a.guide_sha256)


def test_contradiction_priority(root):
    case, gold, note, a = annotated_example(root)
    a.gold_assessments[1].status = "omitted"
    with pytest.raises(ValueError, match="contradiction"):
        validate_alignment(a, note, gold, case, a.guide_sha256)


@pytest.mark.parametrize("change", ["hash", "missing", "duplicate", "unresolved", "citation"])
def test_incomplete_or_forged(root, change):
    case, gold, note, a = annotated_example(root)
    if change == "hash":
        a.note_sha256 = "0" * 64
    if change == "missing":
        a.claims.pop()
    if change == "duplicate":
        a.claims.append(a.claims[0])
    if change == "unresolved":
        a.claims[0].label = "unresolved"
    if change == "citation":
        a.claims[0].citation_assessments = []
    with pytest.raises(ValueError):
        validate_alignment(a, note, gold, case, a.guide_sha256)
