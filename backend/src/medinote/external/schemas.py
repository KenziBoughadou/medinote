from typing import Annotated, Literal

from pydantic import Field, model_validator

from medinote.schemas import (
    DirectAssertion,
    ExtractedFact,
    Identifier,
    Method,
    Model,
    SectionKey,
    Sha256,
)

MAX_ITEMS = 80
MAX_REFERENCE_FACTS = 120

Split = Literal["dev", "test"]
CoverageLabel = Literal["covered", "contradicted", "omitted"]
SupportLabel = Literal["supported", "contradicted", "unsupported"]
JudgeTask = Literal["reference_facts", "coverage", "support"]


class ExternalSegment(Model):
    segment_id: Annotated[str, Field(pattern=r"^s[0-9]{3}$")]
    speaker: Literal["clinician", "patient", "other"]
    speaker_tag: str
    text: Annotated[str, Field(min_length=1, max_length=5000)]


class ExternalCase(Model):
    case_id: Identifier
    split: Split
    subset: Literal["aci", "virtassist", "virtscribe"]
    segments: Annotated[list[ExternalSegment], Field(min_length=2, max_length=200)]
    reference_note: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def segment_order(self):
        if [s.segment_id for s in self.segments] != [
            f"s{i:03}" for i in range(1, len(self.segments) + 1)
        ]:
            raise ValueError("IDs de segments non consécutifs")
        return self


class DirectOutput(Model):
    reason: list[DirectAssertion]
    history: list[DirectAssertion]
    background: list[DirectAssertion]
    medications_allergies: list[DirectAssertion]
    observations: list[DirectAssertion]
    assessment: list[DirectAssertion]
    plan: list[DirectAssertion]

    @model_validator(mode="after")
    def assertion_limit(self):
        if sum(len(getattr(self, key)) for key in SectionKey) > MAX_ITEMS:
            raise ValueError(f"Plus de {MAX_ITEMS} assertions")
        return self


class ExtractionOutput(Model):
    facts: Annotated[list[ExtractedFact], Field(max_length=MAX_ITEMS)]


class ExternalAssertion(Model):
    assertion_id: Identifier
    text: str
    source_ids: list[str]
    unresolved_ids: list[str]


class ExternalSection(Model):
    key: SectionKey
    title: str
    assertions: list[ExternalAssertion]


class ExternalNote(Model):
    case_id: Identifier
    method: Method
    sections: list[ExternalSection]
    text: str
    note_sha256: Sha256

    @property
    def assertions(self):
        return [a for s in self.sections for a in s.assertions]


class ReferenceFact(Model):
    section: SectionKey
    text: Annotated[str, Field(min_length=1, max_length=600)]


class ReferenceFactsOutput(Model):
    facts: Annotated[list[ReferenceFact], Field(max_length=MAX_REFERENCE_FACTS)]


class CoverageJudgment(Model):
    index: Annotated[int, Field(ge=1)]
    label: CoverageLabel


class CoverageOutput(Model):
    judgments: list[CoverageJudgment]


class SupportJudgment(Model):
    index: Annotated[int, Field(ge=1)]
    label: SupportLabel
    citations_support: bool


class SupportOutput(Model):
    judgments: list[SupportJudgment]


class ExternalRun(Model):
    run_id: Identifier
    manifest_sha256: Sha256
    split: Split
    case_id: Identifier
    method: Method
    status: str
    error_code: str | None
    model_requested: str
    model_returned: str | None
    started_at: str
    duration_ms: int
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    raw_response_path: str | None
    note_path: str | None
    note_sha256: Sha256 | None


class JudgeRecord(Model):
    task: JudgeTask
    case_id: Identifier
    method: Method | None
    note_sha256: Sha256 | None
    attempt: Annotated[int, Field(ge=1)]
    status: str
    error_code: str | None
    model_returned: str | None
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    output: dict | None
