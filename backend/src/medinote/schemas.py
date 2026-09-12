from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$", max_length=160)]
SourceId = Annotated[str, Field(min_length=1, max_length=100)]
Text = Annotated[str, Field(min_length=1, max_length=1000)]
SourceIds = Annotated[list[SourceId], Field(max_length=8)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Method(StrEnum):
    direct = "direct"
    structured = "structured"


class SectionKey(StrEnum):
    reason = "reason"
    history = "history"
    background = "background"
    medications_allergies = "medications_allergies"
    observations = "observations"
    assessment = "assessment"
    plan = "plan"


SECTION_TITLES = dict(
    zip(
        SectionKey,
        [
            "Motif",
            "Symptômes et histoire",
            "Antécédents",
            "Traitements et allergies",
            "Observations",
            "Évaluation exprimée",
            "Conduite annoncée",
        ],
        strict=True,
    )
)
Polarity = Literal["affirmed", "negated", "unknown"]
Temporality = Literal["present", "past", "future", "unspecified"]
Certainty = Literal["reported", "observed", "hypothetical", "unspecified"]
SubjectKind = Literal["patient", "relative", "other"]
Speaker = Literal["patient", "clinician", "other"]
OriginKind = Literal["illustrative", "llm_recorded", "llm_live"]
ReviewKind = Literal["none", "ai", "human"]


class SourceSegment(Model):
    segment_id: Annotated[str, Field(pattern=r"^s[0-9]{3}$")]
    speaker: Speaker
    text: Annotated[str, Field(min_length=1, max_length=5000)]


class SourceSpan(Model):
    segment_id: str
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]
    quote: str

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Span vide ou inversé")
        return self


class Subject(Model):
    kind: SubjectKind
    label: Text | None

    @model_validator(mode="after")
    def explicit_subject(self):
        if (self.kind == "patient") != (self.label is None):
            raise ValueError("Patient sans label ; proche et tiers explicitement désignés")
        return self


class StressPairMetadata(Model):
    pair_id: Identifier
    variant: Literal["positive", "negative"]
    target_fact_key: Identifier
    invariant_fact_keys: list[Identifier]


class ConsultationCase(Model):
    schema_version: Literal["1.0"]
    case_id: Identifier
    group_id: Identifier
    family_id: Literal[
        "respiratoire",
        "cardiovasculaire",
        "digestif",
        "urinaire",
        "musculosquelettique",
        "neurologique",
        "dermatologique",
        "suivi-chronique",
        "sante-psychique",
        "prevention",
    ]
    suite: Literal["main", "stress"]
    split: Literal["dev", "test", "stress"]
    title: str
    locale: Literal["fr-FR"]
    segments: Annotated[list[SourceSegment], Field(min_length=8, max_length=24)]
    provenance_id: Identifier
    focus_tags: list[str]
    stress_pair: StressPairMetadata | None

    @model_validator(mode="after")
    def segment_order(self):
        if [s.segment_id for s in self.segments] != [
            f"s{i:03}" for i in range(1, len(self.segments) + 1)
        ]:
            raise ValueError("IDs de segments non consécutifs")
        if (self.suite == "stress") != (self.split == "stress" and self.stress_pair is not None):
            raise ValueError("Suite et métadonnées stress incohérentes")
        return self


class GoldFact(Model):
    fact_id: Identifier
    case_id: Identifier
    fact_key: Identifier
    section: SectionKey
    label: Text
    value: Text | None
    unit: Text | None
    subject: Subject
    polarity: Polarity
    temporality: Temporality
    certainty: Certainty
    expected_in_note: bool
    evidence: Annotated[list[SourceSpan], Field(min_length=1)]


class ProvenanceRecord(Model):
    provenance_id: Identifier
    kind: Literal["ai", "human"]
    author_id: str
    created_at: str
    prompt_sha256: Sha256 | None
    review: ReviewKind


class ReviewEvent(Model):
    artifact_sha256: Sha256
    reviewer_id: str
    kind: Literal["ai", "human"]
    reviewed_at: str
    outcome: Literal["accepted", "changes_requested"]
    remarks: str


class DirectAssertion(Model):
    text: Text
    source_ids: SourceIds


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
        if sum(len(getattr(self, key)) for key in SectionKey) > 40:
            raise ValueError("Plus de 40 assertions")
        return self


class ExtractedFact(Model):
    section: SectionKey
    label: Text
    value: Text | None
    unit: Text | None
    subject: Subject
    polarity: Polarity
    temporality: Temporality
    certainty: Certainty
    source_ids: SourceIds


class ExtractionOutput(Model):
    facts: Annotated[list[ExtractedFact], Field(max_length=40)]


class Citation(Model):
    citation_id: Identifier
    segment_id: str
    resolvable: bool
    quote: str | None


class NoteAssertion(Model):
    assertion_id: Identifier
    text: Text
    citations: Annotated[list[Citation], Field(max_length=8)]


class NoteSection(Model):
    key: SectionKey
    title: str
    assertions: list[NoteAssertion]


class ClinicalNote(Model):
    case_id: Identifier
    sections: list[NoteSection]
    canonical_text: str
    note_sha256: Sha256

    @model_validator(mode="after")
    def layout(self):
        if [s.key for s in self.sections] != list(SectionKey):
            raise ValueError("Les sept rubriques ordonnées sont obligatoires")
        if sum(len(s.assertions) for s in self.sections) > 40:
            raise ValueError("Plus de 40 assertions")
        return self


class TechnicalChecks(Model):
    schema_valid: bool
    references_emitted: int
    references_resolvable: int
    unresolved_ids: list[str]
    assertions_without_citation: list[str]
    warnings: list[str]


class RunMetadata(Model):
    model_requested: str | None
    model_returned: str | None
    prompt_version: str
    prompt_sha256: Sha256
    schema_sha256: Sha256
    renderer_sha256: Sha256
    corpus_sha256: Sha256
    created_at: str
    attempts: Annotated[int, Field(ge=0)]
    input_tokens: Annotated[int, Field(ge=0)] | None
    output_tokens: Annotated[int, Field(ge=0)] | None
    duration_ms: Annotated[int, Field(ge=0)] | None
    estimated_cost_usd: Annotated[float, Field(ge=0)] | None


class Review(Model):
    kind: ReviewKind
    reviewer_id: str | None
    artifact_sha256: Sha256 | None
    reviewed_at: str | None


class MetricValue(Model):
    numerator: int
    denominator: int
    value: float | None


class NoteEvaluation(Model):
    note_sha256: Sha256
    annotation_sha256: Sha256
    metrics: dict[str, MetricValue]


class GenerationResult(Model):
    run_id: Identifier
    case_id: Identifier
    method: Method
    origin: OriginKind
    note: ClinicalNote
    checks: TechnicalChecks
    metadata: RunMetadata
    review: Review
    fidelity_metrics: NoteEvaluation | None

    @model_validator(mode="after")
    def provenance(self):
        if self.case_id != self.note.case_id:
            raise ValueError("Cas discordant")
        if self.origin == "llm_live" and (
            self.review.kind != "none" or self.fidelity_metrics is not None
        ):
            raise ValueError("Une relance live ne reçoit aucune métrique antérieure")
        if self.origin == "illustrative" and any(
            getattr(self.metadata, k) is not None
            for k in (
                "model_requested",
                "model_returned",
                "input_tokens",
                "output_tokens",
                "duration_ms",
                "estimated_cost_usd",
            )
        ):
            raise ValueError("Métadonnées de génération interdites pour une illustration")
        if self.fidelity_metrics and self.fidelity_metrics.note_sha256 != self.note.note_sha256:
            raise ValueError("Métriques d'une autre note")
        if self.review.kind != "none" and self.review.artifact_sha256 != self.note.note_sha256:
            raise ValueError("Revue d'une autre note")
        return self


class GenerateRequest(Model):
    case_id: Identifier
    method: Method


class ErrorDetail(Model):
    code: str
    message: str
    retry_after_seconds: int | None


class ApiError(Model):
    error: ErrorDetail
    request_id: str


class ExampleSummary(Model):
    case_id: str
    title: str
    focus: str
    origins: dict[Method, OriginKind]


class PublicExample(Model):
    consultation: ConsultationCase
    results: dict[Method, GenerationResult]


class Capabilities(Model):
    live_available: bool
    reason: str | None
    methods: list[Method]
    visitor_remaining: int
    global_remaining: int
    next_attempt_at: str | None


class PairedComparison(Model):
    a: float | None
    b: float | None
    difference: float | None
    ci95_low: float | None
    ci95_high: float | None
    n: int
    unit: str
    warnings: list[str]


class PublishedMetrics(Model):
    by_method: dict[Method, dict[str, MetricValue]]
    counts_by_method: dict[Method, dict[str, int]]
    conditional_by_method: dict[Method, dict[str, MetricValue]]
    comparisons: dict[str, PairedComparison]
    stress: dict[Method, MetricValue]
    failures: dict[Method, dict[str, int]]


class PublishedReport(Model):
    schema_version: Literal["1.0"]
    status: Literal[
        "awaiting_runs",
        "awaiting_annotation",
        "awaiting_reference_review",
        "ai_annotated",
        "human_reviewed",
    ]
    cohort_sizes: dict[str, int]
    review_status: dict[str, str]
    metrics: PublishedMetrics | None
    limitations: list[str]
    artifact_links: dict[str, str]
    hashes: dict[str, Sha256]


class PublicBundle(Model):
    schema_version: Literal["1.0"]
    consultations: list[ConsultationCase]
    results: dict[str, dict[Method, GenerationResult]]
    built_at: str
    content_sha256: Sha256
