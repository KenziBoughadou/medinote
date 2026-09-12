import pytest
from evaluation_helpers import annotated_example
from medinote.evaluation.metrics import aggregate_counts, ratio, score_consultation


def test_hand_computed(root):
    _, gold, note, a = annotated_example(root)
    counts = score_consultation(gold, a, note)
    assert {k: counts.get(k, 0) for k in ["E", "C", "K", "O", "P", "U", "D"]} == dict(
        E=2, C=1, K=1, O=0, P=4, U=1, D=1
    )
    values = aggregate_counts([counts])["metrics"]
    assert values["omission"]["value"] == 0
    assert values["coverage"]["value"] == 0.5
    assert values["unsupported"]["value"] == 0.25
    assert values["negation_error"]["value"] == 0.5
    assert values["citation_precision"]["value"] == pytest.approx(2 / 3)
    assert values["resolvable_references"]["value"] == 1


def test_failure_and_null(root):
    _, gold, _, _ = annotated_example(root)
    rows = aggregate_counts([score_consultation(gold, status="timeout")])["metrics"]
    assert rows["omission"]["value"] == 1 and rows["coverage"]["value"] == 0
    assert rows["unsupported"]["value"] is None and rows["citation_precision"]["value"] is None
    assert ratio(0, 0).value is None
