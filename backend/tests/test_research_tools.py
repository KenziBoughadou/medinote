import json

import pytest
from evaluation_helpers import annotated_example
from medinote.schemas import SourceSegment
from medinote.serialization import canonical_json


@pytest.fixture
def modules(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import annotation_review
    import extractive_baselines

    return annotation_review, extractive_baselines


def segments(texts):
    return [
        SourceSegment(segment_id=f"s{i:03}", speaker="patient", text=text)
        for i, text in enumerate(texts, 1)
    ]


def test_centroid_selects_shared_topic_and_retains_original_order(modules):
    _, baseline = modules
    source = segments(["ananas", "toux fièvre", "toux douleur", "toux fièvre douleur"])
    chosen = baseline.select_segments(source, "tfidf_centroid", 2)
    assert [s.segment_id for s in chosen] == ["s002", "s004"]
    assert all(s in source for s in chosen)
    assert baseline.select_segments(source, "lead", 2) == source[:2]


def test_selection_ties_empty_unicode_and_invalid_parameters(modules):
    _, baseline = modules
    source = segments(["écho 🩺", "écho 🩺", "écho 🩺"])
    assert baseline.select_segments(source, "tfidf_centroid", 2) == source[:2]
    assert baseline.select_segments(segments(["!!!", "??"]), "tfidf_centroid", 1)[0].text == "!!!"
    assert baseline.select_segments([], "tfidf_centroid") == []
    with pytest.raises(ValueError):
        baseline.select_segments(source, "tfidf_centroid", 0)


def test_baseline_runs_without_gold_and_never_overwrites(modules, root, tmp_path):
    _, baseline = modules
    fixture = tmp_path / "source"
    (fixture / "data").mkdir(parents=True)
    for name in ("cases.v1.jsonl", "stress.v1.jsonl"):
        (fixture / "data" / name).write_bytes((root / "data" / name).read_bytes())
    output = tmp_path / "results"
    manifest = baseline.run(fixture, output)
    assert manifest["cases"] == 80 and manifest["outputs"] == 160
    assert manifest["provider_calls"] == 0 and manifest["semantic_metrics"] is None
    with pytest.raises(FileExistsError):
        baseline.run(fixture, output)


@pytest.fixture
def blind_fixture(root, tmp_path):
    case, gold, note, annotation = annotated_example(root)
    blind = tmp_path / "blind"
    blind.mkdir()
    doc = {
        "blind_output_id": annotation.blind_output_id,
        "note": note.model_dump(mode="json"),
        "source": case.model_dump(mode="json"),
        "gold": [g.model_dump(mode="json") for g in gold],
    }
    (blind / "blind-0001.json").write_text(canonical_json(doc))
    template = annotation.model_dump(mode="json")
    template.update(
        status="draft", claims=[], gold_assessments=[], segmentation_review_complete=False
    )
    (blind / "annotations-template.jsonl").write_text(canonical_json(template) + "\n")
    return blind, annotation


def test_offline_packs_keep_blinding_and_do_not_create_reviews(
    modules, blind_fixture, root, tmp_path
):
    review, _ = modules
    blind, _ = blind_fixture
    before = (root / "data/review-events.jsonl").read_bytes()
    output = tmp_path / "packs"
    assert review.prepare(blind, root, output) == {"notes": 1, "packs": 1}
    page = (output / "lot-01.html").read_text()
    assert "__REVIEW_DATA__" not in page and "connect-src 'none'" in page
    assert '"method"' not in page and "blind-mapping" not in page
    assert (root / "data/review-events.jsonl").read_bytes() == before


@pytest.mark.parametrize("mutation", [None, "duplicate", "hash", "unfinished", "identity", "span"])
def test_partial_validation_reuses_real_annotation_rules(
    modules,
    blind_fixture,
    root,
    tmp_path,
    mutation,
):
    review, _ = modules
    blind, annotation = blind_fixture
    raw = annotation.model_dump(mode="json")
    if mutation == "hash":
        raw["note_sha256"] = "1" * 64
    elif mutation == "unfinished":
        raw["claims"][0]["label"] = "unresolved"
    elif mutation == "identity":
        raw["annotator"]["id"] = "À RENSEIGNER PAR LE RELECTEUR"
    elif mutation == "span":
        raw["claims"][0]["spans"][0]["quote"] = "Autre texte"
    path = tmp_path / "annotations.jsonl"
    line = canonical_json(raw) + "\n"
    path.write_text(line * (2 if mutation == "duplicate" else 1))
    result = review.check(blind, root, [path])
    assert result["all_complete"] == (mutation is None)
    assert bool(result["errors"]) == (mutation is not None)
    if mutation is None:
        assert result["completed_notes"][0]["annotator_kind"] == "ai"


def test_draft_with_unanswered_fields_is_not_a_completed_review(
    modules, blind_fixture, root, tmp_path
):
    review, _ = modules
    blind, _ = blind_fixture
    raw = json.loads((blind / "annotations-template.jsonl").read_text())
    raw["gold_assessments"] = [{"status": ""}]
    path = tmp_path / "draft.jsonl"
    path.write_text(canonical_json(raw) + "\n")
    result = review.check(blind, root, [path])
    assert result["complete"] == 0 and result["drafts"] == ["blind-0001"]
    assert not result["errors"] and not result["all_complete"]


def test_html_data_cannot_close_its_script_tag(modules, blind_fixture, root, tmp_path):
    review, _ = modules
    blind, _ = blind_fixture
    template_path = blind / "annotations-template.jsonl"
    raw = json.loads(template_path.read_text())
    raw["comments"] = '</script><script>fetch("https://example.invalid")</script>'
    template_path.write_text(canonical_json(raw) + "\n")
    output = tmp_path / "safe"
    review.prepare(blind, root, output)
    page = (output / "lot-01.html").read_text()
    assert raw["comments"] not in page and "\\u003c/script>" in page
