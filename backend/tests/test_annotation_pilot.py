import copy
import json

import pytest
from medinote.evaluation.alignment import validate_annotation_completeness
from medinote.serialization import sha256_file


@pytest.fixture
def pilot(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import compile_annotation_pilot

    folder = root / "eval/results/annotation-pilot-1"
    decisions = json.loads((folder / "decisions.json").read_text())

    def compile_one(bid, rows=None):
        return compile_annotation_pilot.compile_note(
            bid,
            json.loads((folder / "inputs" / f"{bid}.json").read_text()),
            decisions[bid] if rows is None else rows,
            sha256_file(root / "eval/annotation-guide.v1.md"),
            sha256_file(folder / "instructions.md"),
        )

    return compile_annotation_pilot, folder, decisions, compile_one


def test_partial_followup_and_outside_gold_claims_cannot_be_scored_as_complete(pilot):
    _, _, _, compile_one = pilot
    for bid in ("blind-0004", "blind-0010"):
        annotation = compile_one(bid)
        assert annotation.annotator.kind == "ai"
        assert annotation.status == "draft"
        with pytest.raises(ValueError, match="incomplète"):
            validate_annotation_completeness(annotation)
    outside_gold = [c for c in compile_one("blind-0010").claims if not c.gold_ids]
    assert outside_gold
    assert all(c.label == "unresolved" and c.evidence for c in outside_gold)


def test_pilot_rejects_skipped_assertion_false_quote_and_unissued_citation(pilot):
    _, _, decisions, compile_one = pilot
    bid = "blind-0003"
    missing = copy.deepcopy(decisions[bid][:-1])
    with pytest.raises(ValueError, match="pas été examinées"):
        compile_one(bid, missing)
    wrong_quote = copy.deepcopy(decisions[bid])
    wrong_quote[0]["spans"] = [[0, "une phrase inventée"]]
    with pytest.raises(ValueError, match="Extrait absent"):
        compile_one(bid, wrong_quote)
    wrong_citation = copy.deepcopy(decisions[bid])
    wrong_citation[0]["supports"] = ["s012"]
    with pytest.raises(ValueError, match="citation absente"):
        compile_one(bid, wrong_citation)


def test_recompilation_matches_archive_without_creating_human_reviews(pilot, root, tmp_path):
    compiler, folder, _, _ = pilot
    reviews = (root / "data/review-events.jsonl").read_bytes()
    result = compiler.run(root, folder, tmp_path / "compiled")
    for filename in ("annotations.jsonl", "summary.json"):
        assert (tmp_path / "compiled" / filename).read_bytes() == (
            folder / "compiled" / filename
        ).read_bytes()
    assert result["fidelity_metrics"] is None and result["paired_comparison"] is None
    assert (root / "data/review-events.jsonl").read_bytes() == reviews
    with pytest.raises(FileExistsError):
        compiler.run(root, folder, tmp_path / "compiled")
