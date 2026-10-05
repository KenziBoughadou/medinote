"""Requêtes de l'étude externe : génération par A et B, puis jugement automatique."""

import asyncio
import math
import time
from dataclasses import dataclass
from functools import lru_cache, partial
from pathlib import Path

import httpx
import tiktoken
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from openai.lib._pydantic import to_strict_json_schema

from medinote.external.schemas import (
    CoverageOutput,
    DirectOutput,
    ExtractionOutput,
    ReferenceFactsOutput,
    SupportOutput,
)
from medinote.llm import ProviderResult
from medinote.schemas import SECTION_TITLES, Method
from medinote.serialization import canonical_json, sha256_json

PROMPTS = Path(__file__).parent / "prompts"
GENERATOR_MODEL = "gpt-4.1-mini-2025-04-14"
JUDGE_MODEL = "gpt-4.1-2025-04-14"
SECOND_JUDGE_MODEL = "gpt-5-mini-2025-08-07"
JUDGES = {"primary": JUDGE_MODEL, "secondary": SECOND_JUDGE_MODEL}
# USD par million de tokens (entrée, sortie), archivés dans eval/external/pricing.v2.json.
PRICES = {GENERATOR_MODEL: (0.4, 1.6), JUDGE_MODEL: (2.0, 8.0), SECOND_JUDGE_MODEL: (0.25, 2.0)}
MAX_INPUT_TOKENS = 16_000
# Les tokens de raisonnement du second juge sont comptés dans sa sortie.
MAX_OUTPUT_TOKENS = {GENERATOR_MODEL: 8_000, JUDGE_MODEL: 4_000, SECOND_JUDGE_MODEL: 16_000}
# Les modèles à raisonnement n'acceptent pas de température : effort de raisonnement fixé.
MODEL_SETTINGS = {
    GENERATOR_MODEL: {"temperature": 0},
    JUDGE_MODEL: {"temperature": 0},
    SECOND_JUDGE_MODEL: {"reasoning": {"effort": "low"}},
}
# Le bail de génération de l'API dure 75 s : chaque appel doit se terminer avant.
ATTEMPT_TIMEOUT_SECONDS = 70
OUTPUT_TYPES = {Method.direct: DirectOutput, Method.structured: ExtractionOutput}
JUDGE_TYPES = {
    "reference_facts": ReferenceFactsOutput,
    "coverage": CoverageOutput,
    "support": SupportOutput,
}
JUDGE_PROMPTS = {
    "reference_facts": "judge-reference.v2.txt",
    "coverage": "judge-coverage.v2.txt",
    "support": "judge-support.v2.txt",
}


@dataclass(frozen=True)
class ExternalRequest:
    payload: dict
    model: str
    input_tokens: int
    reservation_micro_usd: int
    instructions_sha256: str
    schema_sha256: str


def cost_micro_usd(model, input_tokens, output_tokens):
    if input_tokens is None or output_tokens is None:
        return None
    price_in, price_out = PRICES[model]
    return math.ceil(input_tokens * price_in + output_tokens * price_out)


def pricing(model):
    return partial(cost_micro_usd, model)


@lru_cache
def tokenizer():
    return tiktoken.get_encoding("o200k_base")


def strict_schema(output_type):
    schema = to_strict_json_schema(output_type)
    subject = schema.get("$defs", {}).get("Subject")
    if subject is not None:
        # Même contrainte que la v1 : un patient sans label, un proche ou un tiers nommé.
        label = next(
            variant
            for variant in subject["properties"]["label"]["anyOf"]
            if variant.get("type") == "string"
        )
        schema["$defs"]["Subject"] = {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["patient"]},
                        "label": {"type": "null"},
                    },
                    "required": ["kind", "label"],
                    "additionalProperties": False,
                },
                {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["relative", "other"]},
                        "label": label,
                    },
                    "required": ["kind", "label"],
                    "additionalProperties": False,
                },
            ]
        }
    return schema


def _request(model, instructions, output_type, source):
    schema = strict_schema(output_type)
    payload = {
        "model": model,
        "store": False,
        **MODEL_SETTINGS[model],
        "max_output_tokens": MAX_OUTPUT_TOKENS[model],
        "instructions": instructions,
        "input": [{"role": "user", "content": canonical_json(source)}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": output_type.__name__,
                "strict": True,
                "schema": schema,
            }
        },
    }
    # Majorant : l'enveloppe JSON complète est comptée comme entrée.
    input_tokens = len(tokenizer().encode(canonical_json(payload)))
    if input_tokens > MAX_INPUT_TOKENS:
        raise ValueError(f"Requête trop longue : {input_tokens} tokens")
    reservation = cost_micro_usd(model, input_tokens, MAX_OUTPUT_TOKENS[model])
    return ExternalRequest(
        payload, model, input_tokens, reservation, sha256_json(instructions), sha256_json(schema)
    )


def segments_json(case):
    return [
        {"segment_id": s.segment_id, "speaker": s.speaker, "text": s.text} for s in case.segments
    ]


def generation_request(case, method):
    method = Method(method)
    instructions = (
        (PROMPTS / "common.en.v2.txt").read_text()
        + "\n"
        + (PROMPTS / f"{method}.en.v2.txt").read_text()
    )
    source = {"case_id": case.case_id, "segments": segments_json(case)}
    return _request(GENERATOR_MODEL, instructions, OUTPUT_TYPES[method], source)


def judge_request(task, source, model=JUDGE_MODEL):
    instructions = (PROMPTS / JUDGE_PROMPTS[task]).read_text()
    return _request(model, instructions, JUDGE_TYPES[task], source)


def reference_facts_request(case):
    return judge_request(
        "reference_facts", {"case_id": case.case_id, "reference_note": case.reference_note}
    )


def coverage_request(note, facts, model=JUDGE_MODEL):
    return judge_request(
        "coverage",
        {
            "reference_facts": [
                {"index": i, "section": f.section, "text": f.text} for i, f in enumerate(facts, 1)
            ],
            "note": note.text,
        },
        model,
    )


def support_request(case, note, model=JUDGE_MODEL):
    return judge_request(
        "support",
        {
            "conversation": segments_json(case),
            "assertions": [
                {
                    "index": i,
                    "section": SECTION_TITLES_EN[a.assertion_id.split(".")[0]],
                    "text": a.text,
                    "cited_segments": a.source_ids,
                }
                for i, a in enumerate(note.assertions, 1)
            ],
        },
        model,
    )


SECTION_TITLES_EN = dict(
    zip(
        [key.value for key in SECTION_TITLES],
        [
            "Chief complaint",
            "History of present illness",
            "Past history",
            "Medications and allergies",
            "Exam and results",
            "Assessment",
            "Plan",
        ],
        strict=True,
    )
)


class ExternalProvider:
    def __init__(self, api_key, client=None, timeout_seconds=ATTEMPT_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds
        self.client = client or AsyncOpenAI(
            api_key=api_key, max_retries=0, timeout=httpx.Timeout(timeout_seconds)
        )

    async def close(self):
        await self.client.close()

    async def generate(self, request):
        start = time.monotonic()
        try:
            async with asyncio.timeout(self.timeout_seconds):
                response = await self.client.responses.create(**request.payload)
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
                result.status, result.error_code = "refusal", "PROVIDER_REFUSAL"
            elif response.status == "incomplete" or response.incomplete_details:
                result.status, result.error_code = "truncated", "PROVIDER_TRUNCATED"
            elif response.status != "completed":
                result.status, result.error_code = "api_error", "PROVIDER_UNAVAILABLE"
            else:
                result.output_text = response.output_text
        except (TimeoutError, APITimeoutError):
            result = ProviderResult(status="timeout", error_code="PROVIDER_TIMEOUT")
        except APIStatusError as exc:
            result = ProviderResult(
                status="api_error", error_code="PROVIDER_UNAVAILABLE", http_status=exc.status_code
            )
        except APIConnectionError:
            result = ProviderResult(status="api_error", error_code="PROVIDER_UNAVAILABLE")
        result.duration_ms = round((time.monotonic() - start) * 1000)
        return result
