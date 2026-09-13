import pytest
from evaluation_helpers import annotated_example
from medinote.evaluation.alignment import validate_alignment as validate_v1
from medinote.evaluation.metrics import score_consultation
from medinote.serialization import sha256_file


@pytest.fixture
def amended(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    from annotation_alignment_v1_1 import validate_alignment

    case, gold, note, annotation = annotated_example(root)
    optional = annotation.claims[2]
    optional.gold_ids = []
    annotation.gold_assessments[2].claim_ids = []
    return validate_alignment, case, gold, note, annotation


def test_optional_source_fact_without_gold_is_versioned_and_does_not_change_coverage(
    amended, root
):
    validate, case, gold, note, annotation = amended
    guide = sha256_file(root / "eval/annotation-guide.v1.md")
    with pytest.raises(ValueError, match="Alignement gold requis"):
        validate_v1(annotation, note, gold, case, guide)
    assert validate(annotation, note, gold, case, guide)
    baseline = annotated_example(root)[3]
    assert score_consultation(gold, annotation, note) == score_consultation(gold, baseline, note)


@pytest.mark.parametrize("problem", ["no_evidence", "bad_evidence", "expected", "unresolved"])
def test_amendment_retains_source_and_label_guards(amended, root, problem):
    validate, case, gold, note, annotation = amended
    claim = annotation.claims[2]
    if problem == "no_evidence":
        claim.evidence = []
    elif problem == "bad_evidence":
        claim.evidence[0].quote = "Citation inventée"
    elif problem == "expected":
        claim.label = "supported_expected"
    else:
        claim.label = "unresolved"
    with pytest.raises(ValueError):
        validate(annotation, note, gold, case, sha256_file(root / "eval/annotation-guide.v1.md"))
