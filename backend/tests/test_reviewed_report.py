import json
import shutil

import pytest


@pytest.fixture
def reviewed(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import report_reviewed_v1_1

    return report_reviewed_v1_1, root / "eval/results/reviewed-v1.1"


def test_reviewed_report_is_reproducible_and_preserves_demo_scope(reviewed, root, tmp_path):
    module, folder = reviewed
    report = module.build_report(
        root, root / "eval/results/v1/study", folder / "annotations.jsonl", tmp_path / "report"
    )
    assert report.status == "human_reviewed"
    for name in ("metrics.json", "report.v1.json", "report.md", "bootstrap-indices.json.gz"):
        assert (tmp_path / "report" / name).read_bytes() == (folder / "report" / name).read_bytes()
    counts = report.metrics.counts_by_method
    assert counts["direct"]["E"] == counts["structured"]["E"] == 360
    assert counts["direct"]["C"] == 345 and counts["direct"]["O"] == 15
    assert counts["structured"]["C"] == 333 and counts["structured"]["O"] == 26
    assert counts["structured"]["K"] == 1
    assert report.metrics.comparisons["coverage"].n == 40
    bundle = json.loads((root / "public-data/bundle.v1.json").read_text())
    assert all(
        r["fidelity_metrics"] is None
        for methods in bundle["results"].values()
        for r in methods.values()
    )


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unresolved", "wrong_mapping"])
def test_reviewed_import_rejects_incomplete_or_inconsistent_inputs(
    reviewed, root, tmp_path, problem
):
    module, folder = reviewed
    mapping = json.loads((folder / "blind-mapping.json").read_text())
    rows = [json.loads(line) for line in (folder / "annotations.jsonl").read_text().splitlines()]
    if problem == "missing":
        rows.pop()
    elif problem == "duplicate":
        rows.append(rows[0])
    elif problem == "unresolved":
        rows[0]["claims"][0]["label"] = "unresolved"
    else:
        mapping[rows[0]["blind_output_id"]]["case_id"] = "main-respiratoire-01"
    (tmp_path / "blind-mapping.json").write_text(json.dumps(mapping))
    path = tmp_path / "annotations.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    with pytest.raises(ValueError):
        module.load_validated_annotations(root, root / "eval/results/v1/study", path)


def test_all_three_reference_hashes_need_acceptance(reviewed, root, tmp_path):
    from medinote.publication import validate_report_review
    from medinote.schemas import PublishedReport

    _, folder = reviewed
    report = PublishedReport.model_validate_json((folder / "report/report.v1.json").read_text())
    shutil.copytree(root / "data", tmp_path / "data")
    events = (tmp_path / "data/review-events.jsonl").read_text().splitlines()
    (tmp_path / "data/review-events.jsonl").write_text("\n".join(events[:-1]))
    with pytest.raises(ValueError, match="humaine"):
        validate_report_review(tmp_path, report)
