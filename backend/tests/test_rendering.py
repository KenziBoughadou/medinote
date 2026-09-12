from medinote.rendering import render_extracted_fact
from medinote.schemas import ExtractedFact


def test_fixed_template():
    fact = ExtractedFact(
        section="background",
        label="Dose",
        value="2,5",
        unit="mg",
        subject={"kind": "relative", "label": "père"},
        polarity="negated",
        temporality="past",
        certainty="hypothetical",
        source_ids=[],
    )
    assert render_extracted_fact(fact) == "Dose : 2,5 mg — nié ; proche : père ; passé ; hypothèse."
