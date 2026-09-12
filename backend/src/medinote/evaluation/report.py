import gzip
from collections import Counter

from medinote.corpus import CorpusRepository
from medinote.evaluation.blinding import load_validated_annotations, safe_artifact
from medinote.evaluation.metrics import (
    aggregate_counts,
    paired_bootstrap,
    score_consultation,
    score_stress_pairs,
)
from medinote.evaluation.runner import collect_runs
from medinote.schemas import GenerationResult, Method, PublishedMetrics, PublishedReport
from medinote.serialization import canonical_json, sha256_file, write_json


def assert_report_eligible(runs, annotations):
    required = {r.run_id for r in runs if r.status == "ok"}
    if set(annotations) != required:
        raise ValueError("Annotations finales incomplètes")
    if any(
        a.status == "draft" or any(c.label == "unresolved" for c in a.claims)
        for a in annotations.values()
    ):
        raise ValueError("Annotation non finalisée")
    return True


def build_report(root, batch, annotations_path, output):
    repo = CorpusRepository(root).load()
    runs = collect_runs(batch, root)
    annotations = load_validated_annotations(root, batch, annotations_path)
    assert_report_eligible(runs, annotations)
    output.mkdir(parents=True, exist_ok=False)
    by_method = {}
    conditional = {}
    counts = {}
    failures = {}
    rows = {}
    costs = {}
    expected_test = {c.case_id for c in repo.cases.values() if c.split == "test"}
    expected_stress = {c.case_id for c in repo.cases.values() if c.split == "stress"}
    complete = True
    for method in Method:
        selected = sorted(
            [r for r in runs if r.method == method and repo.get_case(r.case_id).split == "test"],
            key=lambda r: r.case_id,
        )
        if {r.case_id for r in selected} != expected_test:
            complete = False
        rows[method] = []
        valid_rows = []
        for run in selected:
            gold = [g for g in repo.gold if g.case_id == run.case_id]
            note = (
                GenerationResult.model_validate_json(
                    safe_artifact(batch, run.note_path).read_text()
                ).note
                if run.note_path
                else None
            )
            score = score_consultation(gold, annotations.get(run.run_id), note, run.status)
            rows[method].append(score)
            if run.status == "ok":
                valid_rows.append(score)
        agg = aggregate_counts(rows[method])
        by_method[method] = agg["metrics"]
        counts[method] = agg["counts"]
        conditional[method] = aggregate_counts(valid_rows)["metrics"]
        failures[method] = dict(Counter(r.status for r in selected if r.status != "ok"))
        costs[method] = {
            "known_cost_usd": sum(
                r.estimated_cost_usd for r in selected if r.estimated_cost_usd is not None
            ),
            "unknown_cost_runs": sum(r.estimated_cost_usd is None for r in selected),
            "durations_ms": [r.duration_ms for r in selected],
        }
    main_ids = sorted(
        r.case_id
        for r in runs
        if r.method == Method.direct and repo.get_case(r.case_id).split == "test"
    )
    other_ids = sorted(
        r.case_id
        for r in runs
        if r.method == Method.structured and repo.get_case(r.case_id).split == "test"
    )
    if main_ids != other_ids:
        raise ValueError("Comparaison non appariée")
    comparisons = {}
    indices = None
    if set(main_ids) == expected_test:
        comparisons, indices = paired_bootstrap(
            rows[Method.direct], rows[Method.structured], main_ids
        )
        with gzip.GzipFile(
            filename=str(output / "bootstrap-indices.json.gz"), mode="wb", mtime=0
        ) as f:
            f.write(
                canonical_json(
                    {"case_ids": main_ids, "seed": 20260911, "indices": indices.tolist()}
                ).encode()
            )
    stress = {}
    for method in Method:
        sr = [r for r in runs if r.method == method and repo.get_case(r.case_id).split == "stress"]
        if {r.case_id for r in sr} != expected_stress:
            complete = False
        if {r.case_id for r in sr} == expected_stress:
            stress[method] = score_stress_pairs(
                [repo.get_case(r.case_id) for r in sr],
                {r.case_id: annotations.get(r.run_id) for r in sr},
            ).model_dump()
    refs = {
        sha256_file(root / p)
        for p in ["data/cases.v1.jsonl", "data/stress.v1.jsonl", "data/gold.v1.jsonl"]
    }
    reviewed = {
        e.artifact_sha256
        for e in repo.review_events
        if e.kind == "human" and e.outcome == "accepted"
    }
    human_references = refs <= reviewed
    human_outputs = bool(annotations) and all(
        a.annotator.kind == "human" for a in annotations.values()
    )
    status = (
        "awaiting_runs"
        if not complete
        else "ai_annotated"
        if not human_outputs
        else "human_reviewed"
        if human_references
        else "awaiting_reference_review"
    )
    metrics = PublishedMetrics(
        by_method=by_method,
        counts_by_method=counts,
        conditional_by_method=conditional,
        comparisons=comparisons,
        stress=stress,
        failures=failures,
    )
    report = PublishedReport(
        schema_version="1.0",
        status=status,
        cohort_sizes={
            "dev": 20,
            "test": len(main_ids),
            "stress_pairs": 10,
            "recorded_outputs": len(runs),
        },
        review_status={
            "references": "human" if human_references else "ai_prepared_not_human_reviewed",
            "outputs": "human" if human_outputs else "ai",
            "cohorts": "complete" if complete else "incomplete",
        },
        metrics=metrics,
        limitations=[
            "Corpus exclusivement synthétique, sans validation clinique.",
            "Annotation par l’auteur ; aucune indépendance revendiquée.",
            "Le style de B peut compromettre l’aveuglement.",
            "Comparaison des pipelines complets ; le mode de rédaction change aussi.",
            "Les coûts connus sont majorants sans déduction du cache ; les usages manquants restent inconnus.",
        ],
        artifact_links={
            "report": "https://github.com/KenziBoughadou/medinote/blob/main/eval/results/v1/report.md"
        },
        hashes={
            "corpus": repo.corpus_sha256,
            "annotations": sha256_file(annotations_path),
            "manifest": runs[0].manifest_sha256,
        },
    )
    write_json(output / "report.v1.json", report)
    write_json(
        output / "metrics.json",
        {
            "report": report.model_dump(mode="json"),
            "costs": costs,
            "annotators": [a.annotator.model_dump(mode="json") for a in annotations.values()],
        },
    )
    lines = [
        "# MediNote — rapport reproductible",
        "",
        f"Statut : {status}.",
        "",
        "Mesures micro bout en bout ; résultats conditionnels et dénominateurs dans metrics.json.",
        "",
        "| Mesure | A | B | B − A | IC95 |",
        "|---|---|---|---|---|",
    ]

    def fmt(x):
        return "Non évalué" if x is None else f"{x:.4f}"

    for name, c in comparisons.items():
        lines.append(
            f"| {name} | {fmt(c['a'])} | {fmt(c['b'])} | {fmt(c['difference'])} | {fmt(c['ci95_low'])} ; {fmt(c['ci95_high'])} |"
        )
    lines += [
        "",
        "## Limites",
        *["- " + limitation for limitation in report.limitations],
        "",
        "## Observations d’erreur",
    ]
    for run in runs:
        annotation = annotations.get(run.run_id)
        if run.status != "ok" or (
            annotation
            and any(c.label in {"unsupported", "contradiction"} for c in annotation.claims)
        ):
            lines.append(
                f"- {run.case_id} / {run.run_id} : {run.status}. Voir les annotations de cette sortie."
            )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    _figures(output, report, costs)
    return report


def _figures(output, report, costs):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folder = output / "figures"
    folder.mkdir()
    for filename, title, keys in [
        (
            "error-rates.svg",
            "Erreurs des pipelines complets",
            ["omission", "unsupported", "contradiction"],
        ),
        (
            "coverage-cost.svg",
            "Couverture fidèle et coût par tentative",
            ["coverage"],
        ),
        ("stress-pairs.svg", "Réussite des paires de stress", []),
    ]:
        fig, ax = plt.subplots(figsize=(8, 4))
        if filename == "coverage-cost.svg":
            unknown = []
            for i, method in enumerate(Method):
                measure = costs[method]
                attempts = len(measure["durations_ms"])
                coverage = report.metrics.by_method[method]["coverage"].value
                if measure["unknown_cost_runs"] or not attempts or coverage is None:
                    unknown.append(str(method))
                    continue
                cost = measure["known_cost_usd"] / attempts
                ax.scatter(cost, coverage, label=str(method))
                ax.annotate(
                    str(method),
                    (cost, coverage),
                    xytext=(5, 8 + i * 12),
                    textcoords="offset points",
                )
            ax.set_xlabel("Coût moyen estimé par tentative (USD HT, sans remise cache)")
            if unknown:
                ax.text(
                    0.02,
                    0.95,
                    "Coût ou couverture inconnu : " + ", ".join(unknown),
                    transform=ax.transAxes,
                    va="top",
                )
        elif keys:
            for i, method in enumerate(Method):
                vals = [report.metrics.by_method[method][key].value for key in keys]
                for j, v in enumerate(vals):
                    if v is not None:
                        ax.bar(j + i * 0.35, v, width=0.35, label=str(method) if j == 0 else None)
            ax.set_xticks([j + 0.175 for j in range(len(keys))], keys)
        else:
            for i, method in enumerate(Method):
                v = report.metrics.stress.get(method)
                if v is not None and v.value is not None:
                    ax.bar(i, v.value, label=str(method))
            ax.set_xticks([0, 1], ["direct", "structured"])
        ax.set_ylim(0, 1)
        ax.set_title(title)
        ax.set_ylabel("Ratio (valeurs manquantes non tracées)")
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend()
        fig.tight_layout()
        fig.savefig(folder / filename)
        plt.close(fig)
