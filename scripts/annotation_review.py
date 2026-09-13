"""Préparer des lots de relecture hors ligne et valider des annotations partielles."""

import argparse
import json
import re
from pathlib import Path

from medinote.evaluation.alignment import validate_alignment, validate_annotation_completeness
from medinote.evaluation.schemas import Annotation
from medinote.schemas import ClinicalNote, ConsultationCase, GoldFact
from medinote.serialization import canonical_json, sha256_file, sha256_json, write_json


def load_documents(blind, root):
    forms = [
        json.loads(line)
        for line in (blind / "annotations-template.jsonl").read_text().splitlines()
        if line.strip()
    ]
    documents = {}
    guide_hash = sha256_file(root / "eval/annotation-guide.v1.md")
    for form in forms:
        bid = form["blind_output_id"]
        if not re.fullmatch(r"blind-\d{4}", bid) or bid in documents:
            raise ValueError("Identifiant aveugle invalide ou dupliqué")
        doc = json.loads((blind / f"{bid}.json").read_text())
        note = ClinicalNote.model_validate(doc["note"])
        case = ConsultationCase.model_validate(doc["source"])
        gold = [GoldFact.model_validate(row) for row in doc["gold"]]
        if (
            doc["blind_output_id"] != bid
            or note.case_id != case.case_id
            or any(f.case_id != case.case_id for f in gold)
            or form["note_sha256"] != note.note_sha256
            or form["gold_sha256"] != sha256_json([f.model_dump(mode="json") for f in gold])
            or form["guide_sha256"] != guide_hash
        ):
            raise ValueError("Documents et formulaire incompatibles")
        documents[bid] = {"document": doc, "form": form}
    return documents


def prepare(blind, root, output, size=10):
    if not 1 <= size <= 20:
        raise ValueError("Un lot contient entre 1 et 20 notes")
    documents = load_documents(blind, root)
    template = (Path(__file__).parent / "review-workbench.html").read_text()
    output.mkdir(parents=True, exist_ok=False)
    rows = list(documents.values())
    packs = []
    for index in range(0, len(rows), size):
        selected = rows[index : index + size]
        name = f"lot-{len(packs) + 1:02}.html"
        # Le JSON est inerte et les caractères fermant une balise script sont échappés.
        embedded = canonical_json(selected).replace("<", "\\u003c").replace("&", "\\u0026")
        (output / name).write_text(template.replace("__REVIEW_DATA__", embedded))
        packs.append({"file": name, "notes": [row["form"]["blind_output_id"] for row in selected]})
    write_json(
        output / "lots.json", {"notes": len(rows), "packs": packs, "review_status": "not_reviewed"}
    )
    (output / "index.html").write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Relecture MediNote</title>'
        "<h1>Relecture des notes</h1><p>Ouvrir un lot, saisir vos décisions puis exporter le JSONL. "
        "Aucune réponse correcte n’est préremplie. Aucun envoi sur Internet.</p><ul>"
        + "".join(
            f'<li><a href="{p["file"]}">{p["file"]} : {len(p["notes"])} notes</a></li>'
            for p in packs
        )
        + "</ul></html>"
    )
    return {"notes": len(rows), "packs": len(packs)}


def check(blind, root, inputs):
    documents = load_documents(blind, root)
    seen = set()
    annotation_ids = set()
    complete = []
    pending = []
    errors = []
    for path in inputs:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            label = f"{path.name}:{line_number}"
            try:
                raw = json.loads(line)
                bid = raw["blind_output_id"]
                if bid not in documents or bid in seen or raw["annotation_id"] in annotation_ids:
                    raise ValueError("Annotation inconnue ou dupliquée")
                seen.add(bid)
                annotation_ids.add(raw["annotation_id"])
                entry = documents[bid]
                form = entry["form"]
                for field in ("annotation_id", "note_sha256", "gold_sha256", "guide_sha256"):
                    if raw[field] != form[field]:
                        raise ValueError(f"Identité ou empreinte modifiée : {field}")
                if raw["status"] == "draft":
                    pending.append(bid)
                    continue
                annotation = Annotation.model_validate(raw)
                if (
                    not annotation.annotator.id.strip()
                    or "RENSEIGNER" in annotation.annotator.id.upper()
                ):
                    raise ValueError("Identité du relecteur manquante")
                doc = entry["document"]
                validate_annotation_completeness(annotation)
                validate_alignment(
                    annotation,
                    ClinicalNote.model_validate(doc["note"]),
                    [GoldFact.model_validate(f) for f in doc["gold"]],
                    ConsultationCase.model_validate(doc["source"]),
                    form["guide_sha256"],
                )
                complete.append(
                    {"blind_output_id": bid, "annotator_kind": annotation.annotator.kind}
                )
            except (ValueError, KeyError, TypeError) as exc:
                errors.append({"location": label, "message": str(exc)})
    return {
        "expected": len(documents),
        "complete": len(complete),
        "completed_notes": complete,
        "drafts": pending,
        "missing": sorted(set(documents) - seen),
        "errors": errors,
        "all_complete": len(complete) == len(documents) and not errors,
        "notice": "Contrôle de structure et de cohérence ; ne prouve pas une revue humaine réelle.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "check"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--annotations", type=Path, nargs="+")
    parser.add_argument("--size", type=int, default=10)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.output is None:
            parser.error("--output requis")
        result = prepare(args.blind, args.root, args.output, args.size)
    else:
        if not args.annotations:
            parser.error("--annotations requis")
        result = check(args.blind, args.root, args.annotations)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(2 if result.get("errors") else 0)
