import json

import numpy as np
import pytest


@pytest.fixture
def analysis(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import analyze_cost_latency_v1

    return analyze_cost_latency_v1


def test_median_difference_is_not_median_of_paired_differences(analysis):
    a, b = [1, 10, 11], [2, 3, 20]
    indices = np.array([[0, 1, 2], [0, 1, 2]])
    result = analysis.compare(a, b, indices, "median")
    assert result["difference_b_minus_a"] == {"value": -7, "ci95_low": -7, "ci95_high": -7}
    assert result["ratio_b_over_a"]["value"] == 0.3
    result = analysis.compare([1, 2], [2, 4], np.array([[0, 0], [1, 1]]), "mean")
    assert result["difference_b_minus_a"]["value"] == 1.5
    assert result["ratio_b_over_a"] == {"value": 2, "ci95_low": 2, "ci95_high": 2}


@pytest.mark.parametrize("values", [[1, None], [0, 2], [1, float("inf")]])
def test_missing_or_invalid_values_are_not_silently_dropped(analysis, values):
    with pytest.raises(ValueError):
        analysis.compare(values, [1, 2], np.array([[0, 1]]), "mean")


def test_archived_results_reproduce(analysis, root, tmp_path):
    result = analysis.build(root)
    analysis.write(tmp_path / "result", result)
    for name in ("results.json", "README.md", "manifest.json"):
        assert (tmp_path / "result" / name).read_bytes() == (
            root / "eval/results/cost-latency-v1" / name
        ).read_bytes()
    assert result["replications"] == 10000 and len(result["rows"]) == 40
    assert result["measures"]["median_latency"]["difference_b_minus_a"]["value"] == 2.69
    old = json.loads((root / "eval/results/reviewed-v1.1/report/metrics.json").read_text())
    for method, key in (("direct", "a"), ("structured", "b")):
        assert result["measures"]["mean_cost"][key]["value"] == pytest.approx(
            old["costs"][method]["known_cost_usd"] / 40
        )
    with pytest.raises(FileExistsError):
        analysis.write(tmp_path / "result", result)
