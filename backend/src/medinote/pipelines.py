from dataclasses import dataclass

from pydantic import ValidationError

from medinote.llm import OUTPUT_TYPES, GenerationRequest, ProviderResult, build_generation_request
from medinote.rendering import render_direct_output, render_structured_output
from medinote.schemas import ClinicalNote, Method


@dataclass
class PipelineOutcome:
    request: GenerationRequest
    provider: ProviderResult
    note: ClinicalNote | None
    status: str
    error_code: str | None


class DirectPipeline:
    method = Method.direct

    async def run(self, case, provider, request=None):
        request = request or build_generation_request(case, self.method)
        result = await provider.generate(request)
        if result.status != "ok":
            return PipelineOutcome(request, result, None, result.status, result.error_code)
        try:
            output = OUTPUT_TYPES[self.method].model_validate_json(result.output_text or "")
        except (ValidationError, ValueError):
            return PipelineOutcome(request, result, None, "schema_error", "INVALID_OUTPUT")
        try:
            renderer = (
                render_direct_output if self.method == Method.direct else render_structured_output
            )
            note = renderer(case, output)
        except (ValidationError, ValueError):
            return PipelineOutcome(request, result, None, "render_error", "INVALID_OUTPUT")
        return PipelineOutcome(request, result, note, "ok", None)


class StructuredPipeline(DirectPipeline):
    method = Method.structured
