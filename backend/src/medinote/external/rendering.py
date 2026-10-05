import hashlib

from medinote.external.llm import SECTION_TITLES_EN
from medinote.external.schemas import ExternalAssertion, ExternalNote, ExternalSection
from medinote.schemas import Method, SectionKey

POLARITY = {"affirmed": "affirmed", "negated": "negated", "unknown": "unspecified"}
TIME = {
    "present": "current",
    "past": "past",
    "future": "upcoming",
    "unspecified": "timing unspecified",
}
CERTAINTY = {
    "reported": "reported",
    "observed": "observed",
    "hypothetical": "hypothesis",
    "unspecified": "certainty unspecified",
}


def render_extracted_fact(fact):
    subject = (
        "patient"
        if fact.subject.kind == "patient"
        else ("relative" if fact.subject.kind == "relative" else "other")
        + ": "
        + fact.subject.label
    )
    value = f": {fact.value}" if fact.value is not None else ""
    unit = f" {fact.unit}" if fact.unit is not None else ""
    return (
        f"{fact.label}{value}{unit} — {POLARITY[fact.polarity]}; {subject}; "
        f"{TIME[fact.temporality]}; {CERTAINTY[fact.certainty]}."
    )


def _render(case, method, items):
    known = {s.segment_id for s in case.segments}
    sections = []
    for key in SectionKey:
        assertions = [
            ExternalAssertion(
                assertion_id=f"{key}.{i:03}",
                text=text,
                source_ids=source_ids,
                unresolved_ids=[sid for sid in source_ids if sid not in known],
            )
            for i, (text, source_ids) in enumerate(items[key], 1)
        ]
        sections.append(
            ExternalSection(key=key, title=SECTION_TITLES_EN[key], assertions=assertions)
        )
    text = "\n\n".join(s.title + "\n" + "\n".join(a.text for a in s.assertions) for s in sections)
    return ExternalNote(
        case_id=case.case_id,
        method=method,
        sections=sections,
        text=text,
        note_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def render_output(case, method, output):
    if Method(method) == Method.direct:
        items = {key: [(a.text, a.source_ids) for a in getattr(output, key)] for key in SectionKey}
    else:
        items = {key: [] for key in SectionKey}
        for fact in output.facts:
            items[fact.section].append((render_extracted_fact(fact), fact.source_ids))
    return _render(case, Method(method), items)
