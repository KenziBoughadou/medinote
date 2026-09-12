import json

from medinote.config import Settings
from medinote.corpus import CorpusRepository
from medinote.generation import GenerationService
from medinote.llm import ProviderResult
from medinote.schemas import SectionKey
from medinote.usage import UsageStore


async def test_reserved_before_every_retry(root, tmp_path):
    settings = Settings(
        root=root, state_dir=tmp_path, env="test", live_enabled=True, openai_api_key="fake"
    )
    usage = UsageStore(settings.db_path)
    usage.initialize()

    class Provider:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            with usage.connection() as db:
                assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == self.calls
            if self.calls == 1:
                return ProviderResult(status="api_error", http_status=503)
            return ProviderResult(
                status="ok",
                output_text=json.dumps({k: [] for k in SectionKey}),
                input_tokens=5,
                output_tokens=10,
            )

    provider = Provider()
    service = GenerationService(settings, CorpusRepository(root).load(), usage, provider)
    result = await service.generate_public("main-digestif-01", "direct", "h")
    assert provider.calls == 2 and result.metadata.attempts == 2
    assert result.metadata.estimated_cost_usd is None
    assert (
        result.origin == "llm_live"
        and result.fidelity_metrics is None
        and result.review.kind == "none"
    )
    assert usage.get_capabilities("h")["visitor_remaining"] == 4
