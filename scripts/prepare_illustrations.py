"""Prépare des exemples éditoriaux IA, jamais des observations expérimentales."""

from pathlib import Path

from medinote.corpus import CorpusRepository
from medinote.llm import build_generation_request
from medinote.rendering import render_direct_output, render_structured_output
from medinote.schemas import (
    DirectOutput,
    ExtractedFact,
    ExtractionOutput,
    GenerationResult,
    Method,
    Review,
    RunMetadata,
    SectionKey,
)
from medinote.serialization import utc_now, write_json
from medinote.sources import technical_checks


def main():
    root = Path(__file__).resolve().parents[1]
    repo = CorpusRepository(root).load()
    results = {}
    for case in repo.list_public_cases():
        facts = [f for f in repo.gold if f.case_id == case.case_id and f.expected_in_note]
        direct = {k: [] for k in SectionKey}
        extracted = []
        for fact in facts:
            direct[fact.section].append(
                dict(text=fact.evidence[0].quote, source_ids=[s.segment_id for s in fact.evidence])
            )
            extracted.append(
                ExtractedFact(
                    **fact.model_dump(
                        exclude={"fact_id", "case_id", "fact_key", "expected_in_note", "evidence"}
                    ),
                    source_ids=[s.segment_id for s in fact.evidence],
                )
            )
        notes = {
            Method.direct: render_direct_output(case, DirectOutput(**direct)),
            Method.structured: render_structured_output(case, ExtractionOutput(facts=extracted)),
        }
        results[case.case_id] = {}
        for method, note in notes.items():
            req = build_generation_request(case, method)
            result = GenerationResult(
                run_id=f"illustrative-{case.case_id}-{method}-v1",
                case_id=case.case_id,
                method=method,
                origin="illustrative",
                note=note,
                checks=technical_checks(note),
                review=Review(
                    kind="none", reviewer_id=None, artifact_sha256=None, reviewed_at=None
                ),
                fidelity_metrics=None,
                metadata=RunMetadata(
                    model_requested=None,
                    model_returned=None,
                    prompt_version="editorial-v1",
                    prompt_sha256=req.prompt_sha256,
                    schema_sha256=req.schema_sha256,
                    renderer_sha256=req.renderer_sha256,
                    corpus_sha256=repo.corpus_sha256,
                    created_at=utc_now(),
                    attempts=0,
                    input_tokens=None,
                    output_tokens=None,
                    duration_ms=None,
                    estimated_cost_usd=None,
                ),
            )
            results[case.case_id][method] = result.model_dump(mode="json")
    write_json(root / "data/illustrative-notes.v1.json", results)


if __name__ == "__main__":
    main()
