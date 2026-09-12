import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from medinote.corpus import DEMO_IDS
from medinote.errors import ServiceError
from medinote.llm import OpenAIProvider, build_generation_request, estimated_micro_usd
from medinote.pipelines import DirectPipeline, PipelineOutcome, StructuredPipeline
from medinote.schemas import GenerationResult, Method, Review, RunMetadata
from medinote.serialization import utc_now
from medinote.sources import technical_checks


@dataclass
class Execution:
    job_id: str
    result: GenerationResult | None
    outcomes: list[PipelineOutcome]
    started_at: str
    duration_ms: int


class GenerationService:
    def __init__(self, settings, corpus, usage, provider=None):
        self.settings = settings
        self.corpus = corpus
        self.usage = usage
        self._provider = provider
        self._tasks = set()

    def _check_live(self):
        if not self.settings.live_enabled:
            raise ServiceError(
                "LIVE_DISABLED", "Relances IA désactivées ; exemples consultables.", 503
            )
        if self._provider is None:
            self._provider = OpenAIProvider(self.settings.openai_api_key.get_secret_value())

    async def close(self):
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        if isinstance(self._provider, OpenAIProvider):
            await self._provider.close()

    async def generate_public(self, case_id, method, client_key):
        if case_id not in DEMO_IDS:
            raise ServiceError("CASE_NOT_PUBLIC", "Cet exemple n’est pas public.", 404)
        self._check_live()
        task = asyncio.create_task(self._execute(case_id, Method(method), "public", client_key))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        execution = await asyncio.shield(task)
        if execution.result is None:
            outcome = execution.outcomes[-1]
            status = {"timeout": 504, "api_error": 503}.get(outcome.status, 502)
            raise ServiceError(
                outcome.error_code or "INVALID_OUTPUT",
                "La génération a échoué. L’exemple précédent reste consultable.",
                status,
            )
        return execution.result

    async def generate_experiment(self, case_id, method):
        self._check_live()
        if isinstance(self._provider, OpenAIProvider) and (
            self.settings.env != "production"
            or self.settings.db_path != Path("/var/lib/medinote/usage.sqlite3")
        ):
            raise ServiceError(
                "SHARED_BUDGET_REQUIRED",
                "Les campagnes réelles utilisent la comptabilité de production.",
                503,
            )
        return await self._execute(case_id, Method(method), "experiment", None)

    async def _execute(self, case_id, method, channel, client_key):
        case = self.corpus.get_case(case_id)
        request = build_generation_request(case, method)
        job_id = self.usage.acquire_lease(channel, case_id, method)
        started = utc_now()
        start = time.monotonic()
        outcomes = []
        status = "failed"
        pipeline = DirectPipeline() if method == Method.direct else StructuredPipeline()
        attempt_id = None
        try:
            async with asyncio.timeout(55):
                for index in range(2 if channel == "public" else 1):
                    attempt_id = self.usage.reserve_attempt(job_id, client_key, retry=index > 0)
                    try:
                        outcome = await pipeline.run(case, self._provider, request)
                    except BaseException:
                        self.usage.mark_unknown(attempt_id, "INTERRUPTED")
                        raise
                    p = outcome.provider
                    self.usage.settle_attempt(
                        attempt_id, p.input_tokens, p.output_tokens, outcome.error_code
                    )
                    logging.getLogger("medinote.generation").info(
                        "job_id=%s method=%s status=%s duration_ms=%s input_tokens=%s output_tokens=%s",
                        job_id,
                        method,
                        outcome.status,
                        p.duration_ms,
                        p.input_tokens,
                        p.output_tokens,
                    )
                    outcomes.append(outcome)
                    retry = (
                        channel == "public"
                        and index == 0
                        and p.status == "api_error"
                        and p.http_status in {429, 502, 503, 504}
                        and (p.retry_after_seconds is None or p.retry_after_seconds <= 2)
                    )
                    if not retry:
                        break
                    await asyncio.sleep(p.retry_after_seconds or 0)
                result = None
                if outcomes[-1].note:
                    total_in = (
                        sum(o.provider.input_tokens for o in outcomes)
                        if all(o.provider.input_tokens is not None for o in outcomes)
                        else None
                    )
                    total_out = (
                        sum(o.provider.output_tokens for o in outcomes)
                        if all(o.provider.output_tokens is not None for o in outcomes)
                        else None
                    )
                    cost = estimated_micro_usd(total_in, total_out)
                    result = GenerationResult(
                        run_id=uuid4().hex,
                        case_id=case_id,
                        method=method,
                        origin="llm_live" if channel == "public" else "llm_recorded",
                        note=outcomes[-1].note,
                        checks=technical_checks(outcomes[-1].note),
                        review=Review(
                            kind="none", reviewer_id=None, artifact_sha256=None, reviewed_at=None
                        ),
                        fidelity_metrics=None,
                        metadata=RunMetadata(
                            model_requested=request.payload["model"],
                            model_returned=outcomes[-1].provider.model_returned,
                            prompt_version="1.0",
                            prompt_sha256=request.prompt_sha256,
                            schema_sha256=request.schema_sha256,
                            renderer_sha256=request.renderer_sha256,
                            corpus_sha256=self.corpus.corpus_sha256,
                            created_at=started,
                            attempts=len(outcomes),
                            input_tokens=total_in,
                            output_tokens=total_out,
                            duration_ms=round((time.monotonic() - start) * 1000),
                            estimated_cost_usd=cost / 1e6 if cost is not None else None,
                        ),
                    )
                status = outcomes[-1].status
                return Execution(
                    job_id, result, outcomes, started, round((time.monotonic() - start) * 1000)
                )
        except TimeoutError:
            raise ServiceError(
                "PROVIDER_TIMEOUT", "Le délai de génération est dépassé.", 504
            ) from None
        finally:
            self.usage.release_lease(job_id, status)
