import copy
import json

import pytest


@pytest.fixture
def diagnostic(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import analyze_stress_v1

    return analyze_stress_v1


@pytest.fixture
def rows():
    return [
        {
            "method": method,
            "pair_id": "pair-1",
            "variant": variant,
            "target_preserved": not (method == "structured" and variant == "negative"),
            "invariants": {"evaluation": False, "observation": True},
        }
        for method in ("direct", "structured")
        for variant in ("positive", "negative")
    ]


def test_target_success_does_not_hide_missing_invariant(diagnostic, rows):
    result = diagnostic.summarize(rows)
    assert result["direct"]["strict_pairs"]["value"] == 0
    assert result["structured"]["strict_pairs"]["value"] == 0
    assert result["direct"]["target_pairs"]["value"] == 1
    assert result["structured"]["target_pairs"]["value"] == 0
    assert result["structured"]["target_variants"]["value"] == 0.5
    assert result["direct"]["invariants"]["evaluation"]["numerator"] == 0
    assert result["direct"]["invariants"]["observation"]["denominator"] == 2


@pytest.mark.parametrize("problem", ["duplicate", "missing_variant", "invariant_missing"])
def test_rejects_invalid_comparisons(diagnostic, rows, problem):
    rows = copy.deepcopy(rows)
    if problem == "duplicate":
        rows.append(rows[0])
    elif problem == "missing_variant":
        rows = [row for row in rows if row["variant"] == "positive"]
    else:
        del rows[0]["invariants"]["evaluation"]
    with pytest.raises(ValueError):
        diagnostic.summarize(rows)


def test_reproduces_archived_diagnostic_and_preserves_strict_score(diagnostic, root, tmp_path):
    result = diagnostic.build_diagnostic(root)
    assert len(result["rows"]) == 40
    assert result["by_method"]["direct"]["target_pairs"]["numerator"] == 10
    assert result["by_method"]["structured"]["target_pairs"]["numerator"] == 9
    assert result["by_method"]["direct"]["invariants"]["disponibilite"]["numerator"] == 2
    assert result["by_method"]["structured"]["invariants"]["disponibilite"]["numerator"] == 20
    original = json.loads((root / "public-data/report.v1.json").read_text())
    for method in ("direct", "structured"):
        assert result["by_method"][method]["strict_pairs"] == original["metrics"]["stress"][method]
    diagnostic.write_diagnostic(tmp_path / "result", result)
    for name in ("diagnostic.json", "README.md", "manifest.json"):
        assert (tmp_path / "result" / name).read_bytes() == (
            root / "eval/results/stress-diagnostic-v1" / name
        ).read_bytes()
    with pytest.raises(FileExistsError):
        diagnostic.write_diagnostic(tmp_path / "result", result)
