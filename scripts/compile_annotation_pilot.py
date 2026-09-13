"""Compiler des décisions déjà rédigées ; aucun jugement sémantique ni appel IA."""

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from medinote.evaluation.alignment import validate_alignment, validate_annotation_completeness
from medinote.evaluation.schemas import Annotation
from medinote.schemas import ClinicalNote, ConsultationCase, GoldFact
from medinote.serialization import canonical_json, sha256_file, sha256_json, write_json


def compile_note(bid, document, decisions, guide_hash, instructions_hash):
    if not re.fullmatch(r"blind-\d{4}", bid) or document["blind_output_id"] != bid:
        raise ValueError("Identifiant de note invalide")
    note = ClinicalNote.model_validate(document["note"])
    case = ConsultationCase.model_validate(document["source"])
    gold = [GoldFact.model_validate(g) for g in document["gold"]]
    if note.case_id != case.case_id or any(g.case_id != case.case_id for g in gold):
        raise ValueError("Sources et références incompatibles")
    assertions = [a for section in note.sections for a in section.assertions]
    sources = {s.segment_id: s.text for s in case.segments}
    by_key = {g.fact_key: g for g in gold}
    claims = []
    reviewed = set()
    for index, decision in enumerate(decisions, 1):
        cid = f"claim-{index:03}"
        spans = []
        citations = {}
        for selected in decision["spans"]:
            number, quote = selected if isinstance(selected, list) else (selected, None)
            if not isinstance(number, int) or not 0 <= number < len(assertions):
                raise ValueError("Assertion inconnue")
            assertion = assertions[number]
            quote = assertion.text if quote is None else quote
            if not quote or assertion.text.count(quote) != 1:
                raise ValueError("Extrait absent ou ambigu")
            start = assertion.text.index(quote)
            spans.append(
                dict(
                    assertion_id=assertion.assertion_id,
                    start=start,
                    end=start + len(quote),
                    quote=quote,
                )
            )
            citations.update({c.citation_id: c for c in assertion.citations})
            reviewed.add(number)
        reference = by_key[decision["gold"]] if decision["gold"] else None
        label = decision.get(
            "label",
            "supported_expected"
            if reference and reference.expected_in_note
            else "supported_optional",
        )
        evidence = (
            [
                dict(segment_id=sid, start=0, end=len(sources[sid]), quote=sources[sid])
                for sid in decision["evidence"]
            ]
            if "evidence" in decision
            else [s.model_dump() for s in reference.evidence]
            if reference
            else []
        )
        supported = set(decision["supports"])
        if not supported <= {c.segment_id for c in citations.values() if c.resolvable}:
            raise ValueError("Décision portant sur une citation absente ou non résolue")
        claims.append(
            dict(
                claim_id=cid,
                spans=spans,
                normalized_text=" ; ".join(s["quote"] for s in spans),
                label=label,
                gold_ids=[reference.fact_id] if reference else [],
                evidence=evidence,
                contradiction_types=decision.get("contradiction_types", []),
                citation_assessments=[
                    dict(
                        claim_id=cid,
                        citation_id=c.citation_id,
                        resolvable=c.resolvable,
                        supports_claim=c.segment_id in supported,
                        justification=f"{c.segment_id} : {decision['why']}",
                    )
                    for c in citations.values()
                ],
                justification=decision["why"],
            )
        )
    if reviewed != set(range(len(assertions))):
        raise ValueError("Des assertions n'ont pas été examinées")
    assessments = []
    for reference in gold:
        related = [c for c in claims if reference.fact_id in c["gold_ids"]]
        unresolved = any(c["label"] == "unresolved" for c in related)
        status = (
            "not_required"
            if not reference.expected_in_note
            else "contradicted"
            if any(c["label"] == "contradiction" for c in related)
            else "covered"
            if any(c["label"].startswith("supported") for c in related)
            else "omitted"
        )
        why = (
            "Statut provisoire imposé par le schéma v1 : décision non résolue, ne pas noter."
            if unresolved
            else "Fait facultatif, hors dénominateur des faits attendus."
            if not reference.expected_in_note
            else "Voir les décisions des claims associés."
            if related
            else "Aucune restitution de ce fait attendu trouvée dans la note."
        )
        assessments.append(
            dict(
                gold_id=reference.fact_id,
                status=status,
                claim_ids=[c["claim_id"] for c in related],
                justification=why,
            )
        )
    draft = any(c["label"] == "unresolved" for c in claims)
    annotation = Annotation.model_validate(
        dict(
            annotation_id=f"annotation-pilot-1-{bid}",
            blind_output_id=bid,
            note_sha256=note.note_sha256,
            gold_sha256=sha256_json([g.model_dump(mode="json") for g in gold]),
            guide_sha256=guide_hash,
            annotator=dict(
                kind="ai",
                id="codex-session-annotation-pilot-1",
                model_snapshot="GPT-6 (famille annoncée ; snapshot exact non exposé)",
                prompt_sha256=instructions_hash,
            ),
            status="draft" if draft else "complete",
            claims=claims,
            gold_assessments=assessments,
            segmentation_review_complete=True,
            comments="Pilote exploratoire par IA, sans revue humaine. "
            + (
                "Décisions ouvertes : aucun score de fidélité calculable pour cette note."
                if draft
                else "Formulaire IA complet ; aucune validation indépendante ou clinique."
            ),
        )
    )
    if not draft:
        validate_annotation_completeness(annotation)
        validate_alignment(annotation, note, gold, case, guide_hash)
    return annotation


def run(root, experiment, output):
    decisions = json.loads((experiment / "decisions.json").read_text())
    if not decisions:
        raise ValueError("Aucune décision")
    guide_hash = sha256_file(root / "eval/annotation-guide.v1.md")
    instructions_hash = sha256_file(experiment / "instructions.md")
    annotations = []
    inputs = {}
    for bid, rows in decisions.items():
        if not re.fullmatch(r"blind-\d{4}", bid):
            raise ValueError("Identifiant invalide")
        path = experiment / "inputs" / f"{bid}.json"
        annotations.append(
            compile_note(bid, json.loads(path.read_text()), rows, guide_hash, instructions_hash)
        )
        inputs[str(path.relative_to(experiment))] = sha256_file(path)
    output.mkdir(parents=True, exist_ok=False)
    (output / "annotations.jsonl").write_text(
        "".join(canonical_json(a) + "\n" for a in annotations)
    )
    counts = Counter(c.label for a in annotations for c in a.claims)
    summary = dict(
        schema_version="1.0",
        status="ai_annotated_pilot_with_open_decisions",
        notes_examined=len(annotations),
        forms_complete=sum(a.status == "complete" for a in annotations),
        forms_draft=sum(a.status == "draft" for a in annotations),
        claims=sum(counts.values()),
        labels=dict(counts),
        unresolved=[
            dict(note=a.blind_output_id, claim=c.claim_id, reason=c.justification)
            for a in annotations
            for c in a.claims
            if c.label == "unresolved"
        ],
        human_reviews=0,
        additional_provider_calls=0,
        additional_provider_cost_usd=0,
        fidelity_metrics=None,
        paired_comparison=None,
        notice="Compteurs de formulaires, pas scores de performance. "
        "Dix notes exploratoires ; l'étude complète reste en attente.",
    )
    write_json(output / "summary.json", summary)
    write_json(
        output / "manifest.json",
        dict(
            created_at=datetime.now(UTC).isoformat(),
            annotator=annotations[0].annotator.model_dump(),
            selection="Premiers dix identifiants du lot aveugle préexistant ; choix exploratoire post hoc.",
            decisions_sha256=sha256_file(experiment / "decisions.json"),
            compiler_sha256=sha256_file(Path(__file__)),
            guide_sha256=guide_hash,
            inputs=inputs,
            outputs={
                name: sha256_file(output / name) for name in ("annotations.jsonl", "summary.json")
            },
            reproducibility="La compilation des décisions archivées est déterministe ; "
            "leur régénération sémantique dans une session IA ne l'est pas.",
        ),
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--experiment", type=Path, default=Path("eval/results/annotation-pilot-1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.experiment, args.output), ensure_ascii=False, indent=2))
