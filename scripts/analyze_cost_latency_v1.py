"""Intervalles descriptifs post hoc : coût moyen et latence médiane de la campagne v1."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from medinote.corpus import CorpusRepository
from medinote.evaluation.runner import collect_runs
from medinote.serialization import sha256_file, write_json


def compare(a, b, indices, statistic):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not len(a):
        raise ValueError("Observations appariées requises")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a <= 0).any() or (b <= 0).any():
        raise ValueError("Coûts et durées connus, finis et positifs requis")
    if (
        indices.ndim != 2
        or indices.shape[1] != len(a)
        or not np.issubdtype(indices.dtype, np.integer)
    ):
        raise ValueError("Indices de bootstrap incompatibles")
    if indices.min() < 0 or indices.max() >= len(a):
        raise ValueError("Indice hors cohorte")
    aggregate = {"mean": np.mean, "median": np.median}[statistic]
    av, bv = float(aggregate(a)), float(aggregate(b))
    ar, br = aggregate(a[indices], axis=1), aggregate(b[indices], axis=1)

    def interval(value, samples):
        low, high = np.percentile(samples, [2.5, 97.5], method="linear")
        return {"value": float(value), "ci95_low": float(low), "ci95_high": float(high)}

    return {
        "a": interval(av, ar),
        "b": interval(bv, br),
        "difference_b_minus_a": interval(bv - av, br - ar),
        "ratio_b_over_a": interval(bv / av, br / ar),
    }


def build(root):
    index_path = root / "eval/results/reviewed-v1.1/report/bootstrap-indices.json.gz"
    with gzip.open(index_path, "rt") as handle:
        bootstrap = json.load(handle)
    repo = CorpusRepository(root).load()
    case_ids = sorted(c.case_id for c in repo.cases.values() if c.split == "test")
    if bootstrap["case_ids"] != case_ids or len(case_ids) != 40 or bootstrap["seed"] != 20260911:
        raise ValueError("Cohorte ou graine discordante")
    indices = np.asarray(bootstrap["indices"])
    expected = np.random.Generator(np.random.PCG64(20260911)).integers(0, 40, size=(10000, 40))
    if not np.array_equal(indices, expected):
        raise ValueError("Tirages différents du bootstrap archivé")
    runs = collect_runs(root / "eval/results/v1/study", root)
    selected = {(r.method, r.case_id): r for r in runs if r.case_id in case_ids}
    if len(selected) != 80:
        raise ValueError("80 observations requises")
    rows = []
    for case_id in case_ids:
        row = {"case_id": case_id}
        for method in ("direct", "structured"):
            run = selected[method, case_id]
            if run.status != "ok" or run.estimated_cost_usd is None:
                raise ValueError("Échec ou coût inconnu : pas d’exclusion silencieuse")
            row[method] = {
                "run_id": run.run_id,
                "cost_usd": run.estimated_cost_usd,
                "latency_seconds": run.duration_ms / 1000,
            }
        rows.append(row)
    measures = {}
    for name, field, statistic, unit in (
        ("mean_cost", "cost_usd", "mean", "USD"),
        ("median_latency", "latency_seconds", "median", "seconds"),
    ):
        measures[name] = {
            "statistic": statistic,
            "unit": unit,
            **compare(
                [r["direct"][field] for r in rows],
                [r["structured"][field] for r in rows],
                indices,
                statistic,
            ),
        }
    return {
        "analysis": "cost-latency-v1",
        "status": "post_hoc_descriptive",
        "case_count": 40,
        "replications": 10000,
        "seed": 20260911,
        "resampling_unit": "consultation_pair",
        "ci_method": "percentile_2.5_97.5_linear",
        "new_provider_calls": 0,
        "measures": measures,
        "rows": rows,
        "source_hashes": {
            str(p): sha256_file(root / p)
            for p in (
                Path("scripts/analyze_cost_latency_v1.py"),
                Path("eval/results/reviewed-v1.1/report/bootstrap-indices.json.gz"),
                Path("eval/frozen-manifest.v1.json"),
                Path("eval/results/v1/study/main-test/runs.jsonl"),
            )
        },
    }


def write(output, result):
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "results.json", result)
    lines = [
        "# Coût et latence : intervalles de confiance",
        "",
        "Complément descriptif calculé après la campagne v1, sans nouvel appel API.",
        "",
        "| Mesure | A | B | B−A | IC 95 % de B−A | B/A | IC 95 % de B/A |",
        "|---|---:|---:|---:|---|---:|---|",
    ]
    for key, label, digits, unit in (
        ("mean_cost", "Coût moyen par note", 6, "$"),
        ("median_latency", "Latence médiane", 3, "s"),
    ):
        m = result["measures"][key]

        def fmt(x):
            return f"{x:.{digits}f}".replace(".", ",")

        d, r = m["difference_b_minus_a"], m["ratio_b_over_a"]
        lines.append(
            f"| {label} | {fmt(m['a']['value'])} {unit} | {fmt(m['b']['value'])} {unit} | "
            f"{fmt(d['value'])} {unit} | [{fmt(d['ci95_low'])} ; {fmt(d['ci95_high'])}] {unit} | "
            f"{r['value']:.3f} | [{r['ci95_low']:.3f} ; {r['ci95_high']:.3f}] |"
        )
    lines += [
        "",
        "On réutilise exactement les 10 000 tirages du bootstrap de fidélité : 40",
        "consultations tirées avec remise, mêmes indices pour A et B, PCG64 et graine",
        "20260911. À chaque tirage, on recalcule la moyenne des coûts et la médiane",
        "des latences pour chaque méthode, puis B−A et B/A. La différence des médianes",
        "n’est pas la médiane des différences. Les bornes sont les percentiles 2,5 et 97,5.",
        "",
        "Les 80 appels test sont inclus ; aucun coût n’est manquant. Les coûts sont",
        "les estimations archivées avec les tarifs v1, sans remise de cache. Les",
        "intervalles sont conditionnels à ces tarifs et à cette campagne ; ils ne",
        "prédisent pas une facture future. Les latences reflètent les appels enregistrés,",
        "pas des répétitions à différents moments ni une garantie de service. Le coût",
        "d’hébergement et le temps de relecture ne sont pas inclus.",
        "",
        "Ce calcul décrit la variabilité entre consultations. Il ne mesure ni la",
        "variation entre plusieurs générations d’un même cas, ni la généralisation",
        "à un autre modèle ou corpus. Les intervalles de A et B sont aussi disponibles",
        "dans [les résultats détaillés](results.json), avec les 40 paires et les empreintes.",
        "",
        "Reproduction depuis la racine, vers un dossier neuf :",
        "",
        "```bash",
        "uv run python scripts/analyze_cost_latency_v1.py --output .state/cost-latency-v1",
        "```",
        "",
    ]
    (output / "README.md").write_text("\n".join(lines))
    write_json(
        output / "manifest.json",
        {
            "source_hashes": result["source_hashes"],
            "files": {name: sha256_file(output / name) for name in ("results.json", "README.md")},
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root)
    write(args.output, result)
    print(json.dumps(result["measures"], ensure_ascii=False, indent=2))
