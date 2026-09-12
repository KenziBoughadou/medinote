from fastapi import APIRouter, Request

from medinote.client_identity import request_client_key
from medinote.corpus import DEMO_IDS
from medinote.errors import ServiceError
from medinote.health import check_readiness
from medinote.schemas import (
    ApiError,
    Capabilities,
    ExampleSummary,
    GenerateRequest,
    GenerationResult,
    PublicExample,
    PublishedReport,
)

router = APIRouter(
    prefix="/api",
    responses={code: {"model": ApiError} for code in [403, 404, 413, 415, 422, 429, 502, 503, 504]},
)


def public_data(request):
    if request.app.state.bundle is None:
        raise ServiceError("PUBLIC_DATA_UNAVAILABLE", "Exemples temporairement indisponibles.", 503)
    return request.app.state.bundle


@router.get("/health/ready", response_model=dict[str, str])
def ready(request: Request):
    if not check_readiness(request.app.state.settings, request.app.state.usage):
        raise ServiceError("NOT_READY", "Service temporairement indisponible.", 503)
    return {"status": "ok"}


@router.get("/examples", response_model=list[ExampleSummary])
def list_examples(request: Request):
    bundle = public_data(request)
    return [
        ExampleSummary(
            case_id=c.case_id,
            title=c.title,
            focus={
                "main-digestif-01": "Cas simple",
                "main-respiratoire-01": "Négation",
                "main-cardiovasculaire-01": "Antécédent familial",
                "main-neurologique-01": "Incertitude",
                "main-musculosquelettique-01": "Correction",
                "main-prevention-01": "Médicament",
            }[c.case_id],
            origins={m: r.origin for m, r in bundle.results[c.case_id].items()},
        )
        for c in bundle.consultations
    ]


@router.get("/examples/{case_id}", response_model=PublicExample)
def get_example(case_id: str, request: Request):
    if case_id not in DEMO_IDS:
        raise ServiceError("CASE_NOT_PUBLIC", "Cet exemple n’est pas public.", 404)
    bundle = public_data(request)
    return PublicExample(
        consultation=next(c for c in bundle.consultations if c.case_id == case_id),
        results=bundle.results[case_id],
    )


@router.get("/capabilities", response_model=Capabilities)
def get_capabilities(request: Request):
    state = request.app.state
    reason = None
    try:
        key = request_client_key(request)
    except ServiceError as exc:
        key = None
        reason = exc.message
    if state.usage is None:
        return Capabilities(
            live_available=False,
            reason="Comptabilité indisponible.",
            methods=["direct", "structured"],
            visitor_remaining=0,
            global_remaining=0,
            next_attempt_at=None,
        )
    caps = state.usage.get_capabilities(key)
    if not state.settings.live_enabled:
        reason = "Relances IA désactivées ; exemples consultables."
    if reason:
        caps.update(live_available=False, reason=reason)
    return Capabilities(**caps)


def generation_identity(request: Request):
    if not request.app.state.settings.live_enabled:
        raise ServiceError("LIVE_DISABLED", "Relances IA désactivées ; exemples consultables.", 503)
    return request_client_key(request)


@router.post("/generate", response_model=GenerationResult)
async def generate_note(body: GenerateRequest, request: Request):
    if body.case_id not in DEMO_IDS:
        raise ServiceError("CASE_NOT_PUBLIC", "Cet exemple n’est pas public.", 404)
    # Dependency override is injectable in ASGI tests only, with no HTTP switch.
    dependency = request.app.dependency_overrides.get(generation_identity, generation_identity)
    key = dependency(request)
    if request.app.state.generation is None:
        raise ServiceError("NOT_READY", "Service temporairement indisponible.", 503)
    return await request.app.state.generation.generate_public(body.case_id, body.method, key)


@router.get("/report", response_model=PublishedReport)
def get_report(request: Request):
    public_data(request)
    return request.app.state.report
