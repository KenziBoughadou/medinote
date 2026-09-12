"""Exporter les références pour relecture, sans créer d’événement humain ni de gel."""

import argparse
import html
from pathlib import Path

from medinote.corpus import CorpusRepository
from medinote.serialization import sha256_file, write_json


def prepare(root: Path, output: Path):
    repo = CorpusRepository(root).load()
    repo.validate_corpus()
    hashes = {
        name: sha256_file(root / name)
        for name in ("data/cases.v1.jsonl", "data/stress.v1.jsonl", "data/gold.v1.jsonl")
    }
    output.mkdir(parents=True, exist_ok=False)
    escape = html.escape
    for split in ("dev", "test", "stress"):
        cases = sorted((c for c in repo.cases.values() if c.split == split), key=lambda c: c.case_id)
        parts = [
            '<!doctype html><html lang="fr"><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>MediNote — relecture {split}</title>",
            "<style>body{font:18px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:0 24px}"
            "article{border-top:2px solid #555;margin-top:48px}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
            "li{margin-bottom:12px}code{overflow-wrap:anywhere}</style><main>",
            f"<h1>Références {split} — {len(cases)} consultations fictives</h1>",
            "<p>Préparées par IA, relecture humaine en attente. Cet export ne vaut ni acceptation "
            "des références, ni validation clinique, ni gel expérimental.</p>",
            "<p>Vérifier chaque preuve et tous les champs du fait : sujet, valeur, polarité, "
            "temps, certitude et caractère attendu. Consigner les désaccords avec le case_id "
            "et le fact_id. Ne confirmer un fichier qu’après sa relecture entière.</p>",
            "<p>Seuls les vingt cas dev servent aux ajustements des prompts. Les fichiers test "
            "et stress servent à la relecture des références, sans ajustement du générateur.</p>",
            "<nav><ul>",
        ]
        parts += [f'<li><a href="#{c.case_id}">{c.case_id}</a></li>' for c in cases]
        parts.append("</ul></nav>")
        for case in cases:
            parts.append(f'<article id="{case.case_id}"><h2>{case.case_id}</h2><h3>Dialogue intégral</h3>')
            for segment in case.segments:
                parts.append(
                    f"<p><strong>{segment.segment_id} · {segment.speaker}</strong><br>"
                    f"{escape(segment.text)}</p>"
                )
            parts.append("<h3>Faits de référence et preuves exactes</h3>")
            for fact in (f for f in repo.gold if f.case_id == case.case_id):
                parts.append(f"<h4>{fact.fact_id}</h4><pre>{escape(fact.model_dump_json(indent=2))}</pre>")
            parts.append("</article>")
        parts.append("<h2>Empreintes des fichiers à relire</h2><ul>")
        parts += [f"<li>{name}<br><code>{digest}</code></li>" for name, digest in hashes.items()]
        parts.append("</ul></main></html>")
        (output / f"{split}.html").write_text("\n".join(parts), encoding="utf-8")
    write_json(output / "reference-hashes.json", hashes)
    return hashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.root, args.output)
    print(f"Relecture préparée dans {args.output}. Aucun événement humain créé.")
