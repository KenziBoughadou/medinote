"""Rapport de relecture v1.1, sur les sorties immuables de v1.

Agrégation conservée depuis evaluation/report.py ; chargement des annotations
avec le validateur amendé et mapping publié après clôture de la relecture.
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

from annotation_alignment_v1_1 import validate_alignment, validate_annotation_completeness
from medinote.corpus import CorpusRepository, read_jsonl
from medinote.evaluation.blinding import safe_artifact
from medinote.evaluation.metrics import (
    aggregate_counts,
    paired_bootstrap,
    score_consultation,
    score_stress_pairs,
)
from medinote.evaluation.report import _figures, assert_report_eligible
from medinote.evaluation.runner import collect_runs
from medinote.evaluation.schemas import Annotation
from medinote.schemas import GenerationResult, Method, PublishedMetrics, PublishedReport
from medinote.serialization import canonical_json, sha256_file, write_json


def load_validated_annotations(root, batch, path):
    repo = CorpusRepository(root).load()
    runs = collect_runs(batch, root)
    by_id = {run.run_id: run for run in runs}
    mapping = json.loads((path.parent / "blind-mapping.json").read_text())
    if len(mapping) != len(runs) or {row["run_id"] for row in mapping.values()} != set(by_id):
        raise ValueError("Mapping incomplet ou dupliqué")
    result = {}
    seen = set()
    identifiers = set()
    for annotation in read_jsonl(path, Annotation):
        bid = annotation.blind_output_id
        if bid not in mapping or bid in seen or annotation.annotation_id in identifiers:
            raise ValueError("Annotation inconnue ou dupliquée")
        seen.add(bid)
        identifiers.add(annotation.annotation_id)
        mapped = mapping[bid]
        run = by_id[mapped["run_id"]]
        if (mapped["case_id"], mapped["method"], mapped["note_path"]) != (
            run.case_id,
            run.method,
            run.note_path,
        ):
            raise ValueError("Mapping et campagne discordants")
        if run.status != "ok" or run.note_path is None:
            raise ValueError("Annotation sans note valide")
        note = GenerationResult.model_validate_json(
            safe_artifact(batch, run.note_path).read_text()
        ).note
        gold = [g for g in repo.gold if g.case_id == run.case_id]
        validate_annotation_completeness(annotation)
        if not annotation.annotator.id.strip() or "RENSEIGNER" in annotation.annotator.id.upper():
            raise ValueError("Identité du relecteur absente")
        validate_alignment(
            annotation,
            note,
            gold,
            repo.get_case(run.case_id),
            sha256_file(root / "eval/annotation-guide.v1.md"),
        )
        result[run.run_id] = annotation
    if seen != {bid for bid, row in mapping.items() if row["note_path"]}:
        raise ValueError("Annotations finales incomplètes")
    for method in Method:
        for split in ("test", "stress"):
            expected = {c.case_id for c in repo.cases.values() if c.split == split}
            actual = {
                r.case_id
                for r in runs
                if r.method == method and repo.get_case(r.case_id).split == split
            }
            if actual != expected:
                raise ValueError("Cohorte incomplète")
    return result


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
            "Alignement v1.1 amendé après observation : faits facultatifs sourcés admis hors références.",
            "Décisions de Kenzi, relecteur unique ; les contrôles logiciels ne vérifient pas leur justesse sémantique.",
            "Faits de référence parfois composés et segmentation déclarée : une couverture partielle peut être surestimée.",
            "Les intervalles bootstrap mesurent la variabilité entre cas, pas l’incertitude de l’annotation.",
        ],
        artifact_links={
            "report": "https://github.com/KenziBoughadou/medinote/blob/main/eval/results/reviewed-v1.1/report/report.md"
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--batch", type=Path, default=Path("eval/results/v1/study"))
    parser.add_argument(
        "--annotations", type=Path, default=Path("eval/results/reviewed-v1.1/annotations.jsonl")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.root, args.batch, args.annotations, args.output)
    write_json(
        args.output / "reproduction-manifest.json",
        {
            "validator_sha256": sha256_file(
                Path(__file__).with_name("annotation_alignment_v1_1.py")
            ),
            "report_script_sha256": sha256_file(Path(__file__)),
            "mapping_sha256": sha256_file(args.annotations.parent / "blind-mapping.json"),
            "review_events_sha256": sha256_file(args.root / "data/review-events.jsonl"),
            "report_sha256": sha256_file(args.output / "report.v1.json"),
            "metrics_sha256": sha256_file(args.output / "metrics.json"),
            "hashes": report.hashes,
            "evaluation_version": "1.1",
        },
    )
    print(
        canonical_json(
            {
                "status": report.status,
                "cohort_sizes": report.cohort_sizes,
                "comparisons": report.metrics.model_dump(mode="json")["comparisons"],
                "stress": report.metrics.model_dump(mode="json")["stress"],
            }
        )
    )
