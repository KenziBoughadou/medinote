"""Comparateurs extractifs exploratoires ; aucune dépendance au gold ni appel fournisseur."""

import argparse
import html
import json
import math
import re
from collections import Counter
from pathlib import Path

from medinote.schemas import ConsultationCase
from medinote.serialization import canonical_json, sha256_file, sha256_json, utc_now, write_json

METHODS = ("lead", "tfidf_centroid")


def normalized(vector):
    length = math.sqrt(sum(value * value for value in vector.values()))
    return {key: value / length for key, value in vector.items()} if length else {}


def select_segments(segments, method, k=5):
    if method not in METHODS or type(k) is not int or k < 1:
        raise ValueError("Méthode inconnue ou nombre de segments invalide")
    if not segments:
        return []
    if method == "lead":
        return list(segments[:k])
    counts = [Counter(re.findall(r"\w+", segment.text.casefold())) for segment in segments]
    df = Counter(token for row in counts for token in row)
    vectors = [
        normalized(
            {
                token: count * (1 + math.log((1 + len(segments)) / (1 + df[token])))
                for token, count in row.items()
            }
        )
        for row in counts
    ]
    centroid = Counter()
    for vector in vectors:
        centroid.update(vector)
    centroid = normalized(centroid)
    scores = [sum(value * centroid[token] for token, value in row.items()) for row in vectors]
    chosen = sorted(sorted(range(len(segments)), key=lambda i: (-scores[i], i))[:k])
    return [segments[i] for i in chosen]


def run(root, output, k=5):
    if type(k) is not int or k < 1:
        raise ValueError("k doit être un entier positif")
    inputs = ("data/cases.v1.jsonl", "data/stress.v1.jsonl")
    cases = [
        ConsultationCase.model_validate_json(line)
        for name in inputs
        for line in (root / name).read_text().splitlines()
        if line
    ]
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Consultations dupliquées")
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for case in sorted(cases, key=lambda c: c.case_id):
        source_words = sum(len(s.text.split()) for s in case.segments)
        for method in METHODS:
            selected = select_segments(case.segments, method, k)
            segments = [s.model_dump(mode="json") for s in selected]
            records.append(
                {
                    "case_id": case.case_id,
                    "split": case.split,
                    "method": method,
                    "k": k,
                    "source_sha256": sha256_json(
                        [s.model_dump(mode="json") for s in case.segments]
                    ),
                    "segments": segments,
                    "output_sha256": sha256_json(segments),
                    "source_words": source_words,
                    "selected_words": sum(len(s.text.split()) for s in selected),
                    "provider_calls": 0,
                    "api_cost_usd": 0,
                    "review": "none",
                    "semantic_metrics": None,
                }
            )
    (output / "outputs.jsonl").write_text("".join(canonical_json(r) + "\n" for r in records))
    manifest = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "experiment": "extractive-posthoc-1",
        "scope": "Exploratoire après publication de v1 ; pas un nouveau test indépendant",
        "methods": list(METHODS),
        "k": k,
        "cases": len(cases),
        "outputs": len(records),
        "files": {name: sha256_file(root / name) for name in inputs},
        "script_sha256": sha256_file(Path(__file__)),
        "outputs_sha256": sha256_file(output / "outputs.jsonl"),
        "provider_calls": 0,
        "semantic_metrics": None,
    }
    write_json(output / "manifest.json", manifest)
    lines = [
        "# Comparateurs extractifs exploratoires",
        "",
        f"{len(cases)} consultations, {len(records)} extraits, aucun appel IA.",
        "",
        f"Chaque sortie recopie au plus {k} tours de parole (paramètre k dans le manifest), "
        "en conservant le locuteur et l’ordre original. Aucun fait gold ne sert à la sélection.",
        "",
        "| Ensemble | Méthode | Sorties | Mots conservés / mots source |",
        "|---|---|---:|---:|",
    ]
    for split in ("dev", "test", "stress"):
        for method in METHODS:
            rows = [r for r in records if r["split"] == split and r["method"] == method]
            total = sum(r["source_words"] for r in rows)
            ratio = sum(r["selected_words"] for r in rows) / total if total else 0
            lines.append(f"| {split} | {method} | {len(rows)} | {ratio:.1%} |")
    lines += [
        "",
        "Ce ratio mesure la longueur, pas la couverture des faits ni la qualité.",
        "",
        "Ces méthodes peuvent retenir une question sans sa réponse, perdre une négation "
        "située dans un autre tour ou omettre une information rare. Copier le texte ne garantit "
        "pas une synthèse fidèle. Il n’y a ni note en sept rubriques ni score sémantique final.",
        "",
        "Comparaison ajoutée après v1 : ne pas fusionner ses sorties avec les 132 appels "
        "figés. Une comparaison de fidélité avec A/B nécessite une annotation dédiée.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    parts = [
        '<!doctype html><html lang="fr"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Comparateurs extractifs MediNote</title>",
        "<style>body{font:18px/1.6 system-ui;max-width:1100px;margin:2rem auto;padding:1rem}"
        "section{border-top:1px solid #777}article{padding:1rem;border:1px solid #ccc}"
        "pre{white-space:pre-wrap}</style><main><h1>Extraits sans modèle génératif</h1>",
        "<p>Consultations fictives. Sorties non évaluées humainement. "
        "Les questions restent des questions, les locuteurs sont conservés.</p>",
    ]
    for case in sorted(cases, key=lambda c: c.case_id):
        parts.append(
            f"<section><h2>{html.escape(case.case_id)}</h2><details><summary>Dialogue complet</summary>"
        )
        for segment in case.segments:
            parts.append(
                f"<p>{html.escape(segment.segment_id)} · {html.escape(segment.speaker)}"
                f"<br>{html.escape(segment.text)}</p>"
            )
        parts.append("</details>")
        for row in (r for r in records if r["case_id"] == case.case_id):
            parts.append(f"<article><h3>{row['method']}</h3>")
            for segment in row["segments"]:
                parts.append(
                    f"<p>{html.escape(segment['segment_id'])} · {html.escape(segment['speaker'])}"
                    f"<br>{html.escape(segment['text'])}</p>"
                )
            parts.append("</article>")
        parts.append("</section>")
    (output / "comparison.html").write_text("\n".join(parts) + "</main></html>\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.output, args.k), indent=2))
