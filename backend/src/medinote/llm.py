import asyncio
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import httpx
import tiktoken
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from openai.lib._pydantic import to_strict_json_schema

from medinote.config import MODEL_ID
from medinote.errors import ServiceError
from medinote.schemas import DirectOutput, ExtractionOutput, Method
from medinote.serialization import canonical_json, sha256_file, sha256_json

PROMPTS = Path(__file__).parent / "prompts"
OUTPUT_TYPES = {Method.direct: DirectOutput, Method.structured: ExtractionOutput}


@dataclass(frozen=True)
class GenerationRequest:
    payload: dict
    method: Method
    prompt_sha256: str
    schema_sha256: str
    renderer_sha256: str


@dataclass
class ProviderResult:
    status: str
    raw_json: dict | None = None
    output_text: str | None = None
    response_id: str | None = None
    model_returned: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_ms: int = 0
    error_code: str | None = None
    http_status: int | None = None
    retry_after_seconds: float | None = None


class LLMProvider(Protocol):
    async def generate(self, request: GenerationRequest) -> ProviderResult: ...


def build_generation_request(case, method: Method) -> GenerationRequest:
    method = Method(method)
    instructions = (
        (PROMPTS / "common.v1.txt").read_text() + "\n" + (PROMPTS / f"{method}.v1.txt").read_text()
    )
    schema = to_strict_json_schema(OUTPUT_TYPES[method])
    source = {
        "case_id": case.case_id,
        "locale": case.locale,
        "segments": [s.model_dump() for s in case.segments],
    }
    payload = {
        "model": MODEL_ID,
        "store": False,
        "temperature": 0,
        "max_output_tokens": 4000,
        "instructions": instructions,
        "input": [{"role": "user", "content": canonical_json(source)}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": OUTPUT_TYPES[method].__name__,
                "strict": True,
                "schema": schema,
            }
        },
    }
    request = GenerationRequest(
        payload,
        method,
        sha256_json(instructions),
        sha256_json(schema),
        sha256_file(Path(__file__).parent / "rendering.py"),
    )
    validate_input_budget(request)
    return request


@lru_cache
def tokenizer():
    return tiktoken.encoding_for_model(MODEL_ID)


def validate_input_budget(request):
    encoded = canonical_json(request.payload)
    # SDK httpx uses compact UTF-8 JSON; include the entire envelope in both limits.
    if len(encoded.encode("utf-8")) > 24000 or len(tokenizer().encode(encoded)) > 6000:
        raise ServiceError("INPUT_TOO_LARGE", "Consultation hors des limites autorisées.", 422)


def estimated_micro_usd(input_tokens, output_tokens):
    if input_tokens is None or output_tokens is None:
        return None
    return math.ceil((input_tokens * 2 + output_tokens * 8) / 5)


class OpenAIProvider:
    def __init__(self, api_key: str, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI(
            api_key=api_key, max_retries=0, timeout=httpx.Timeout(25)
        )

    async def close(self):
        await self.client.close()

    async def generate(self, request):
        start = time.monotonic()
        result = ProviderResult(status="api_error", error_code="PROVIDER_UNAVAILABLE")
        try:
            async with asyncio.timeout(25):
                response = await self.client.responses.create(**request.payload)
            # Usage and complete raw response are captured before local parsing.
            result = ProviderResult(
                status="ok",
                raw_json=response.model_dump(mode="json"),
                response_id=response.id,
                model_returned=response.model,
                input_tokens=response.usage.input_tokens if response.usage else None,
                output_tokens=response.usage.output_tokens if response.usage else None,
            )
            refusal = any(
                getattr(c, "type", None) == "refusal"
                for item in response.output
                for c in getattr(item, "content", [])
            )
            if refusal:
                result.status = "refusal"
                result.error_code = "PROVIDER_REFUSAL"
            elif response.status == "incomplete" or response.incomplete_details:
                result.status = "truncated"
                result.error_code = "PROVIDER_TRUNCATED"
            elif response.status != "completed":
                result.status = "api_error"
                result.error_code = "PROVIDER_UNAVAILABLE"
            else:
                result.output_text = response.output_text
        except (TimeoutError, APITimeoutError):
            result = ProviderResult(status="timeout", error_code="PROVIDER_TIMEOUT")
        except APIStatusError as exc:
            retry = exc.response.headers.get("retry-after")
            # An unparseable/HTTP-date Retry-After is conservatively not retried.
            try:
                retry = float(retry) if retry is not None else None
                if retry is not None and (not math.isfinite(retry) or retry < 0):
                    retry = math.inf
            except ValueError:
                retry = math.inf
            result = ProviderResult(
                status="api_error",
                error_code="PROVIDER_UNAVAILABLE",
                http_status=exc.status_code,
                retry_after_seconds=retry,
            )
        except APIConnectionError:
            result = ProviderResult(status="api_error", error_code="PROVIDER_UNAVAILABLE")
        result.duration_ms = round((time.monotonic() - start) * 1000)
        return result
