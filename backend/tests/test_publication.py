import json

import pytest
from medinote.publication import validate_bundle


def test_tamper(root):
    value = json.loads((root / "public-data/bundle.v1.json").read_text())
    value["consultations"][0]["segments"][0]["text"] = "forged"
    with pytest.raises(ValueError, match="Hash"):
        validate_bundle(value)


def test_human_label_requires_reference_events(root):
    from medinote.publication import validate_report_review
    from medinote.schemas import PublishedReport

    report = PublishedReport.model_validate_json((root / "public-data/report.v1.json").read_text())
    report.status = "human_reviewed"
    with pytest.raises(ValueError, match="humaine"):
        validate_report_review(root, report)


def test_recorded_demos_can_publish_before_annotation(root, tmp_path):
    from medinote.publication import build_public_bundle

    value = json.loads((root / "data/illustrative-notes.v1.json").read_text())
    for methods in value.values():
        for result in methods.values():
            result["origin"] = "llm_recorded"
            result["metadata"].update(
                model_requested="gpt-4.1-mini-2025-04-14",
                model_returned="gpt-4.1-mini-2025-04-14",
                attempts=1,
                input_tokens=100,
                output_tokens=10,
                duration_ms=1,
                estimated_cost_usd=0.000056,
            )
    bundle, report = build_public_bundle(root, results=value, output=tmp_path)
    assert report.status == "awaiting_annotation" and report.metrics is None
    assert report.cohort_sizes["demo_recorded_outputs"] == 12
    assert all(
        result.fidelity_metrics is None
        for methods in bundle.results.values()
        for result in methods.values()
    )
