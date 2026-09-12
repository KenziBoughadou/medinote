from medinote.schemas import SECTION_TITLES, NoteAssertion, NoteSection, SectionKey
from medinote.sources import finalize_note, resolve_citations

POLARITY = {"affirmed": "affirmé", "negated": "nié", "unknown": "non précisé"}
TIME = {
    "present": "actuel",
    "past": "passé",
    "future": "à venir",
    "unspecified": "temporalité non précisée",
}
CERTAINTY = {
    "reported": "rapporté",
    "observed": "observé",
    "hypothetical": "hypothèse",
    "unspecified": "certitude non précisée",
}


def render_extracted_fact(fact):
    subject = (
        "patient"
        if fact.subject.kind == "patient"
        else (
            ("proche" if fact.subject.kind == "relative" else "tiers") + " : " + fact.subject.label
        )
    )
    value = f" : {fact.value}" if fact.value is not None else ""
    unit = f" {fact.unit}" if fact.unit is not None else ""
    return (
        f"{fact.label}{value}{unit} — {POLARITY[fact.polarity]} ; {subject} ; "
        f"{TIME[fact.temporality]} ; {CERTAINTY[fact.certainty]}."
    )


def _render(case, items):
    sections = []
    for key, title in SECTION_TITLES.items():
        assertions = []
        for i, (text, source_ids) in enumerate(items[key], 1):
            aid = f"{key}.{i:03}"
            assertions.append(
                NoteAssertion(
                    assertion_id=aid, text=text, citations=resolve_citations(case, source_ids, aid)
                )
            )
        sections.append(NoteSection(key=key, title=title, assertions=assertions))
    return finalize_note(case.case_id, sections)


def render_direct_output(case, output):
    return _render(
        case, {key: [(a.text, a.source_ids) for a in getattr(output, key)] for key in SectionKey}
    )


def render_structured_output(case, output):
    items = {key: [] for key in SectionKey}
    for fact in output.facts:
        items[fact.section].append((render_extracted_fact(fact), fact.source_ids))
    return _render(case, items)
