from medinote.serialization import sha256_json
from medinote.sources import validate_source_span


def validate_alignment(annotation, note, gold, case, guide_sha256):
    if (
        annotation.note_sha256 != note.note_sha256
        or annotation.gold_sha256 != sha256_json([f.model_dump(mode="json") for f in gold])
        or annotation.guide_sha256 != guide_sha256
    ):
        raise ValueError("Hash annotation/note/gold/guide discordant")
    assertions = {a.assertion_id: a for s in note.sections for a in s.assertions}
    gold_by_id = {g.fact_id: g for g in gold}
    claims = {c.claim_id: c for c in annotation.claims}
    if len(claims) != len(annotation.claims):
        raise ValueError("Claim dupliqué")
    normalized = [c.normalized_text.casefold().strip() for c in annotation.claims]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Regrouper les répétitions en un claim à plusieurs spans")
    covered_assertions = set()
    for claim in annotation.claims:
        if claim.label == "unresolved":
            raise ValueError("Une décision unresolved empêche le rapport final")
        if not set(claim.gold_ids) <= set(gold_by_id):
            raise ValueError("Gold inconnu")
        if (
            claim.label in {"supported_expected", "supported_optional", "contradiction"}
            and not claim.gold_ids
        ):
            raise ValueError("Alignement gold requis")
        if claim.label.startswith("supported") and not claim.evidence:
            raise ValueError("Preuve source requise")
        if (claim.label == "contradiction") != bool(claim.contradiction_types):
            raise ValueError("Types de contradiction incohérents")
        if claim.label == "supported_expected" and not all(
            gold_by_id[g].expected_in_note for g in claim.gold_ids
        ):
            raise ValueError("Fait facultatif étiqueté attendu")
        if claim.label == "supported_optional" and any(
            gold_by_id[g].expected_in_note for g in claim.gold_ids
        ):
            raise ValueError("Fait attendu étiqueté facultatif")
        citations = {}
        for span in claim.spans:
            assertion = assertions.get(span.assertion_id)
            if (
                assertion is None
                or span.end <= span.start
                or span.end > len(assertion.text)
                or assertion.text[span.start : span.end] != span.quote
            ):
                raise ValueError("Span de note invalide")
            covered_assertions.add(span.assertion_id)
            citations.update({c.citation_id: c for c in assertion.citations})
        for span in claim.evidence:
            validate_source_span(case, span)
        assessments = {a.citation_id: a for a in claim.citation_assessments}
        if len(assessments) != len(claim.citation_assessments) or set(assessments) != set(
            citations
        ):
            raise ValueError("Chaque association claim–citation doit être évaluée")
        for cid, a in assessments.items():
            if (
                a.claim_id != claim.claim_id
                or a.resolvable != citations[cid].resolvable
                or (a.supports_claim and not a.resolvable)
            ):
                raise ValueError("Contrôle de citation incohérent")
    if covered_assertions != set(assertions):
        raise ValueError("Assertions sans revue de segmentation")
    assessments = {g.gold_id: g for g in annotation.gold_assessments}
    if set(assessments) != set(gold_by_id) or len(assessments) != len(annotation.gold_assessments):
        raise ValueError("Un statut final unique par fait gold est requis")
    for gid, a in assessments.items():
        expected = gold_by_id[gid].expected_in_note
        related = [c for c in annotation.claims if gid in c.gold_ids]
        if set(a.claim_ids) != {c.claim_id for c in related}:
            raise ValueError("Alignement bidirectionnel discordant")
        contradiction = any(c.label == "contradiction" for c in related)
        supported = any(c.label in {"supported_expected", "supported_optional"} for c in related)
        expected_status = (
            "not_required"
            if not expected
            else "contradicted"
            if contradiction
            else "covered"
            if supported
            else "omitted"
        )
        if a.status != expected_status:
            raise ValueError("Une contradiction prime sur une couverture simultanée")
    return True


def validate_annotation_completeness(annotation):
    if (
        annotation.status not in {"complete", "adjudicated"}
        or not annotation.segmentation_review_complete
    ):
        raise ValueError("Annotation incomplète")
    if any(c.label == "unresolved" for c in annotation.claims):
        raise ValueError("Décision non résolue")
