import json

import pytest
from medinote.corpus import CorpusRepository
from medinote.llm import ProviderResult
from medinote.pipelines import DirectPipeline, StructuredPipeline
from medinote.schemas import SectionKey


class Provider:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def generate(self, request):
        self.calls.append(request)
        return self.result


@pytest.mark.parametrize(
    "pipeline,data",
    [(DirectPipeline, {k: [] for k in SectionKey}), (StructuredPipeline, {"facts": []})],
)
async def test_one_call(root, pipeline, data):
    case = CorpusRepository(root).load().list_public_cases()[0]
    provider = Provider(ProviderResult(status="ok", output_text=json.dumps(data)))
    outcome = await pipeline().run(case, provider)
    assert outcome.status == "ok" and len(provider.calls) == 1
    assert provider.calls[0].payload["store"] is False
    assert provider.calls[0].payload["model"] == "gpt-4.1-mini-2025-04-14"


@pytest.mark.parametrize("status", ["timeout", "refusal", "truncated", "api_error"])
async def test_failure_no_fallback(root, status):
    case = CorpusRepository(root).load().list_public_cases()[0]
    provider = Provider(ProviderResult(status=status))
    outcome = await DirectPipeline().run(case, provider)
    assert outcome.status == status and outcome.note is None and len(provider.calls) == 1


async def test_invalid_retains_usage(root):
    case = CorpusRepository(root).load().list_public_cases()[0]
    provider = Provider(
        ProviderResult(status="ok", output_text="invalid", input_tokens=10, output_tokens=20)
    )
    outcome = await DirectPipeline().run(case, provider)
    assert outcome.status == "schema_error" and outcome.provider.output_tokens == 20
