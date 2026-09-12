from medinote.corpus import CorpusRepository
from medinote.evaluation.schemas import Annotation
from medinote.rendering import render_direct_output
from medinote.schemas import DirectOutput, SectionKey
from medinote.serialization import sha256_file, sha256_json


def annotated_example(root):
    repo = CorpusRepository(root).load()
    case = repo.get_case("main-respiratoire-01")
    keys = ["motif", "signe-cible", "disponibilite"]
    gold = [f for f in repo.gold if f.case_id == case.case_id and f.fact_key in keys]
    by_key = {g.fact_key: g for g in gold}
    texts = [
        by_key["motif"].evidence[0].quote,
        "Fièvre présente.",
        by_key["disponibilite"].evidence[0].quote,
        "Antibiotique prescrit.",
    ]
    refs = [["s002"], ["s006"], ["s012"], []]
    data = {k: [] for k in SectionKey}
    data["history"] = [{"text": t, "source_ids": r} for t, r in zip(texts, refs, strict=True)]
    note = render_direct_output(case, DirectOutput(**data))
    labels = ["supported_expected", "contradiction", "supported_optional", "unsupported"]
    claims = []
    for i, (a, label) in enumerate(zip(note.sections[1].assertions, labels, strict=True)):
        key = keys[i] if i < 3 else None
        claims.append(
            {
                "claim_id": f"claim-{i}",
                "spans": [
                    {
                        "assertion_id": a.assertion_id,
                        "start": 0,
                        "end": len(a.text),
                        "quote": a.text,
                    }
                ],
                "normalized_text": a.text,
                "label": label,
                "gold_ids": [by_key[key].fact_id] if key else [],
                "evidence": [s.model_dump() for s in by_key[key].evidence]
                if label.startswith("supported")
                else [],
                "contradiction_types": ["polarity"] if label == "contradiction" else [],
                "citation_assessments": [
                    {
                        "claim_id": f"claim-{i}",
                        "citation_id": c.citation_id,
                        "resolvable": True,
                        "supports_claim": label.startswith("supported"),
                        "justification": "Lecture manuelle du cas miniature de test.",
                    }
                    for c in a.citations
                ],
                "justification": "Fixture synthétique, aucun résultat expérimental.",
            }
        )
    annotation = Annotation(
        annotation_id="fixture",
        blind_output_id="blind-0001",
        note_sha256=note.note_sha256,
        gold_sha256=sha256_json([g.model_dump(mode="json") for g in gold]),
        guide_sha256=sha256_file(root / "eval/annotation-guide.v1.md"),
        annotator={
            "kind": "ai",
            "id": "fixture",
            "model_snapshot": "simulated-test",
            "prompt_sha256": "0" * 64,
        },
        status="complete",
        claims=claims,
        gold_assessments=[
            {
                "gold_id": by_key[k].fact_id,
                "status": status,
                "claim_ids": [f"claim-{i}"],
                "justification": "Fixture de calcul.",
            }
            for i, (k, status) in enumerate(
                zip(keys, ["covered", "contradicted", "not_required"], strict=True)
            )
        ],
        segmentation_review_complete=True,
        comments="Fixture sans annotation humaine réelle.",
    )
    return case, gold, note, annotation
