from typing import Annotated, Literal

from pydantic import Field, model_validator

from medinote.schemas import Method, Model, Sha256, SourceSpan


class FrozenManifest(Model):
    schema_version: Literal["1.0"]
    created_at: str
    code_sha: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    files: dict[str, Sha256]
    parameters: dict
    suites: dict[str, list[tuple[str, Method]]]
    reference_review: Literal["none", "ai", "human"]
    reference_hashes: dict[str, Sha256]


class ExperimentRun(Model):
    batch_id: str
    run_id: str
    case_id: str
    method: Method
    manifest_sha256: Sha256
    hashes: dict[str, Sha256]
    model_requested: str
    model_returned: str | None
    parameters: dict
    started_at: str
    duration_ms: int
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    status: Literal[
        "ok", "api_error", "timeout", "refusal", "truncated", "schema_error", "render_error"
    ]
    error_code: str | None
    raw_response_path: str | None
    note_path: str | None


class Annotator(Model):
    kind: Literal["ai", "human"]
    id: Annotated[str, Field(min_length=1)]
    model_snapshot: str | None
    prompt_sha256: Sha256 | None

    @model_validator(mode="after")
    def provenance(self):
        if self.kind == "ai" and (not self.model_snapshot or not self.prompt_sha256):
            raise ValueError("Une annotation IA exige modèle et prompt identifiés")
        if self.kind == "human" and (
            self.model_snapshot is not None or self.prompt_sha256 is not None
        ):
            raise ValueError("Une annotation IA ne devient pas humaine en changeant son étiquette")
        return self


class AssertionSpan(Model):
    assertion_id: str
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]
    quote: str


class CitationAssessment(Model):
    claim_id: str
    citation_id: str
    resolvable: bool
    supports_claim: bool
    justification: Annotated[str, Field(min_length=1)]


class AnnotatedClaim(Model):
    claim_id: str
    spans: Annotated[list[AssertionSpan], Field(min_length=1)]
    normalized_text: Annotated[str, Field(min_length=1)]
    label: Literal[
        "supported_expected", "supported_optional", "contradiction", "unsupported", "unresolved"
    ]
    gold_ids: list[str]
    evidence: list[SourceSpan]
    contradiction_types: list[
        Literal["polarity", "value", "subject", "temporality", "certainty", "other"]
    ]
    citation_assessments: list[CitationAssessment]
    justification: Annotated[str, Field(min_length=1)]


class GoldAssessment(Model):
    gold_id: str
    status: Literal["covered", "contradicted", "omitted", "not_required"]
    claim_ids: list[str]
    justification: Annotated[str, Field(min_length=1)]


class Annotation(Model):
    annotation_id: str
    blind_output_id: str
    note_sha256: Sha256
    gold_sha256: Sha256
    guide_sha256: Sha256
    annotator: Annotator
    status: Literal["draft", "complete", "adjudicated"]
    claims: list[AnnotatedClaim]
    gold_assessments: list[GoldAssessment]
    segmentation_review_complete: bool
    comments: str
