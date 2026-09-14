"""Diagnostic post hoc du stress v1, sans modifier le score strict ni les annotations."""

import argparse
from collections import defaultdict
from pathlib import Path

from medinote.corpus import CorpusRepository
from medinote.evaluation.metrics import ratio, score_stress_pairs
from medinote.evaluation.runner import collect_runs
from medinote.serialization import sha256_file, write_json
from report_reviewed_v1_1 import load_validated_annotations


def summarize(rows):
    """Séparer cible et invariants ; une paire exige toujours ses deux variantes."""
    methods = defaultdict(dict)
    for row in rows:
        key = (row["pair_id"], row["variant"])
        if row["method"] not in {"direct", "structured"} or key in methods[row["method"]]:
            raise ValueError("Méthode inconnue ou variante dupliquée")
        methods[row["method"]][key] = row
    if set(methods) != {"direct", "structured"}:
        raise ValueError("Deux méthodes requises")
    if set(methods["direct"]) != set(methods["structured"]):
        raise ValueError("Cohortes non appariées")
    keys = set(next(iter(methods["direct"].values()))["invariants"])
    if not keys or any(set(row["invariants"]) != keys for row in rows):
        raise ValueError("Invariants discordants")
    result = {}
    for method, variants in sorted(methods.items()):
        pairs = defaultdict(list)
        for row in variants.values():
            pairs[row["pair_id"]].append(row)
        if any({r["variant"] for r in pair} != {"positive", "negative"} for pair in pairs.values()):
            raise ValueError("Paire incomplète")
        values = list(variants.values())
        n = len(values)
        result[method] = {
            "target_variants": ratio(sum(r["target_preserved"] for r in values), n).model_dump(),
            "target_pairs": ratio(
                sum(all(r["target_preserved"] for r in pair) for pair in pairs.values()),
                len(pairs),
            ).model_dump(),
            "strict_pairs": ratio(
                sum(
                    all(r["target_preserved"] and all(r["invariants"].values()) for r in pair)
                    for pair in pairs.values()
                ),
                len(pairs),
            ).model_dump(),
            "invariants": {
                key: ratio(sum(r["invariants"][key] for r in values), n).model_dump()
                for key in sorted(keys)
            },
        }
    return result


def fact_preserved(annotation, fact_id):
    assessment = next(a for a in annotation.gold_assessments if a.gold_id == fact_id)
    if assessment.status == "not_required":
        return any(
            fact_id in claim.gold_ids and claim.label == "supported_optional"
            for claim in annotation.claims
        )
    return assessment.status == "covered"


def build_diagnostic(root):
    batch = root / "eval/results/v1/study"
    annotation_path = root / "eval/results/reviewed-v1.1/annotations.jsonl"
    annotations = load_validated_annotations(root, batch, annotation_path)
    repo = CorpusRepository(root).load()
    cases = sorted((c for c in repo.cases.values() if c.split == "stress"), key=lambda c: c.case_id)
    runs = {(r.method, r.case_id): r for r in collect_runs(batch, root)}
    rows = []
    for method in ("direct", "structured"):
        for case in cases:
            run = runs[method, case.case_id]
            annotation = annotations[run.run_id]
            meta = case.stress_pair
            rows.append(
                {
                    "case_id": case.case_id,
                    "method": method,
                    "pair_id": meta.pair_id,
                    "variant": meta.variant,
                    "blind_output_id": annotation.blind_output_id,
                    "note_path": str(Path("eval/results/v1/study") / run.note_path),
                    "target_fact_key": meta.target_fact_key,
                    "target_preserved": fact_preserved(
                        annotation, f"{case.case_id}.{meta.target_fact_key}"
                    ),
                    "invariants": {
                        key: fact_preserved(annotation, f"{case.case_id}.{key}")
                        for key in meta.invariant_fact_keys
                    },
                }
            )
    summary = summarize(rows)
    for method in ("direct", "structured"):
        strict = score_stress_pairs(
            cases, {c.case_id: annotations[runs[method, c.case_id].run_id] for c in cases}
        ).model_dump()
        if summary[method]["strict_pairs"] != strict:
            raise ValueError("Le diagnostic diverge du score strict v1")
    sources = [
        "data/cases.v1.jsonl",
        "data/stress.v1.jsonl",
        "data/gold.v1.jsonl",
        "data/review-events.jsonl",
        "eval/frozen-manifest.v1.json",
        "eval/results/reviewed-v1.1/annotations.jsonl",
        "eval/results/reviewed-v1.1/blind-mapping.json",
        "scripts/annotation_alignment_v1_1.py",
        "scripts/report_reviewed_v1_1.py",
        "scripts/analyze_stress_v1.py",
    ]
    return {
        "analysis": "stress-diagnostic-v1",
        "status": "post_hoc_descriptive",
        "source_release": "v1",
        "annotation_version": "1.1",
        "new_provider_calls": 0,
        "source_hashes": {path: sha256_file(root / path) for path in sources},
        "by_method": summary,
        "rows": rows,
    }


def write_diagnostic(output, report):
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "diagnostic.json", report)
    lines = [
        "# Ce que mesure le test de stress",
        "",
        "Ce diagnostic est ajouté après observation des résultats de v1. Il décompose les",
        "annotations existantes sans changer le score strict, les notes ou les références.",
        "Aucun nouvel appel au modèle. Ces mesures sont descriptives et ne sont pas un",
        "nouveau benchmark indépendant.",
        "",
        "| Mesure | A direct | B structuré |",
        "|---|---:|---:|",
    ]
    labels = {
        "strict_pairs": "Paires réussies au critère strict initial",
        "target_pairs": "Paires avec le fait cible conservé dans les deux variantes",
        "target_variants": "Notes avec le fait cible conservé",
    }
    for key, label in labels.items():
        values = [report["by_method"][m][key] for m in ("direct", "structured")]
        lines.append(
            f"| {label} | "
            + " | ".join(f"{v['numerator']} / {v['denominator']}" for v in values)
            + " |"
        )
    lines += [
        "",
        "Le fait cible est celui dont la polarité change entre les deux variantes.",
        "« Conservé » signifie que l’annotation le classe comme couvert ; ce critère porte",
        "sur le fait entier, pas uniquement sur le mot de négation. Une omission échoue",
        "aussi. Les 20 notes par méthode correspondent à dix paires, pas à vingt cas",
        "indépendants. On ne calcule pas de nouvel intervalle ni de classement global.",
        "",
        "## Conservation des faits invariants",
        "",
        "Chaque ligne porte sur les 20 variantes par méthode. La disponibilité reste",
        "facultative dans le test principal, mais fait partie du critère strict de stress.",
        "Une assertion facultative doit être sourcée et reliée à sa référence pour compter.",
        "",
        "| Fait invariant | A direct | B structuré |",
        "|---|---:|---:|",
    ]
    for key in report["by_method"]["direct"]["invariants"]:
        values = [report["by_method"][m]["invariants"][key] for m in ("direct", "structured")]
        lines.append(
            f"| {key} | "
            + " | ".join(f"{v['numerator']} / {v['denominator']}" for v in values)
            + " |"
        )
    lines += [
        "",
        "## Comment lire ces résultats",
        "",
        "L’omission systématique de l’évaluation exprimée suffit à faire échouer toutes",
        "les paires au score strict. Ce score a donc peu de pouvoir pour départager les",
        "méthodes sur ces données. Le détail permet de distinguer cette omission du",
        "traitement du fait cible, sans sélectionner seulement les faits réussis.",
        "",
        "Le découpage est post hoc, le corpus est synthétique et une seule personne a",
        "annoté les notes. Les résultats restent dépendants de ces décisions. Pour une",
        "nouvelle campagne, il faudrait définir les dimensions à mesurer avant les appels,",
        "tester leur sensibilité sur le développement puis les figer pour un nouveau jeu.",
        "",
        "[Détail des 40 notes](diagnostic.json) · [Empreintes](manifest.json) ·",
        "[Méthodologie](../../../docs/HUMAN_REVIEW_RESULTS.md)",
        "",
        "Pour refaire le diagnostic depuis la racine, dans un nouveau dossier :",
        "",
        "```bash",
        "uv run python scripts/analyze_stress_v1.py --output .state/stress-diagnostic-v1",
        "```",
        "",
    ]
    (output / "README.md").write_text("\n".join(lines))
    write_json(
        output / "manifest.json",
        {
            "analysis": report["analysis"],
            "status": report["status"],
            "source_hashes": report["source_hashes"],
            "files": {
                name: sha256_file(output / name) for name in ("diagnostic.json", "README.md")
            },
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    diagnostic = build_diagnostic(args.root)
    write_diagnostic(args.output, diagnostic)
    print("Diagnostic post hoc écrit ; score strict v1 conservé, aucun appel fournisseur.")
