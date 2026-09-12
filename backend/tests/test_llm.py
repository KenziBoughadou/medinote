import json

import httpx
import pytest
from medinote.corpus import CorpusRepository
from medinote.llm import OpenAIProvider, build_generation_request, estimated_micro_usd
from openai import AsyncOpenAI


async def test_sdk_no_retry(root):
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            429,
            headers={"retry-after": "2"},
            json={"error": {"message": "limited", "type": "rate_limit"}},
        )

    client = AsyncOpenAI(
        api_key="test-not-a-secret",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
    )
    provider = OpenAIProvider("unused", client)
    result = await provider.generate(
        build_generation_request(CorpusRepository(root).load().list_public_cases()[0], "direct")
    )
    await provider.close()
    assert result.http_status == 429 and result.retry_after_seconds == 2
    assert len(requests) == 1 and requests[0]["text"]["format"]["strict"] is True


def test_cost_unknown():
    assert estimated_micro_usd(None, 100) is None
    assert estimated_micro_usd(100, 100) == 200


@pytest.mark.parametrize("kind", ["completed", "refusal", "truncated"])
async def test_sdk_usage_before_validation(root, kind):
    fixture = json.loads((root / "backend/tests/fixtures/provider-responses.json").read_text())[
        "completed_empty"
    ]
    if kind == "refusal":
        fixture["output"][0]["content"] = [{"type": "refusal", "refusal": "Fixture de refus"}]
    if kind == "truncated":
        fixture["status"] = "incomplete"
        fixture["incomplete_details"] = {"reason": "max_output_tokens"}
    client = AsyncOpenAI(
        api_key="test",
        max_retries=0,
        http_client=httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=fixture))
        ),
    )
    provider = OpenAIProvider("unused", client)
    result = await provider.generate(
        build_generation_request(CorpusRepository(root).load().list_public_cases()[0], "direct")
    )
    await provider.close()
    assert result.input_tokens == 100 and result.output_tokens == 50
    assert (
        result.status == {"completed": "ok", "refusal": "refusal", "truncated": "truncated"}[kind]
    )
    assert result.raw_json["id"] == "resp_fixture"
