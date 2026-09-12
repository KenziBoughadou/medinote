import hashlib

from medinote.schemas import Citation, ClinicalNote, TechnicalChecks


def validate_source_span(case, span):
    segment = next((s for s in case.segments if s.segment_id == span.segment_id), None)
    if (
        segment is None
        or span.end > len(segment.text)
        or segment.text[span.start : span.end] != span.quote
    ):
        raise ValueError("Preuve source discordante")


def resolve_citations(case, source_ids, assertion_id):
    sources = {s.segment_id: s.text for s in case.segments}
    return [
        Citation(
            citation_id=f"{assertion_id}.c{i:03}",
            segment_id=sid,
            resolvable=sid in sources,
            quote=sources.get(sid),
        )
        for i, sid in enumerate(source_ids, 1)
    ]


def build_canonical_note(sections):
    return "\n\n".join(s.title + "\n" + "\n".join(a.text for a in s.assertions) for s in sections)


def finalize_note(case_id, sections):
    text = build_canonical_note(sections)
    return ClinicalNote(
        case_id=case_id,
        sections=sections,
        canonical_text=text,
        note_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def technical_checks(note):
    citations = [c for s in note.sections for a in s.assertions for c in a.citations]
    missing = [a.assertion_id for s in note.sections for a in s.assertions if not a.citations]
    unresolved = [c.segment_id for c in citations if not c.resolvable]
    duplicate = [
        a.assertion_id
        for s in note.sections
        for a in s.assertions
        if len({c.segment_id for c in a.citations}) < len(a.citations)
    ]
    warnings = []
    if missing:
        warnings.append("Assertions sans citation")
    if unresolved:
        warnings.append("Références non résolues")
    if duplicate:
        warnings.append("Références dupliquées : " + ", ".join(duplicate))
    return TechnicalChecks(
        schema_valid=True,
        references_emitted=len(citations),
        references_resolvable=sum(c.resolvable for c in citations),
        unresolved_ids=unresolved,
        assertions_without_citation=missing,
        warnings=warnings,
    )
