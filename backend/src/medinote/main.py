import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from medinote.config import Settings
from medinote.corpus import CorpusRepository
from medinote.errors import register_error_handlers
from medinote.generation import GenerationService
from medinote.http_security import RequestLimitsMiddleware
from medinote.publication import load_public
from medinote.routes import router
from medinote.usage import UsageStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()

    @asynccontextmanager
    async def lifespan(app):
        try:
            app.state.bundle, app.state.report = load_public(settings.root)
            corpus = CorpusRepository(settings.root).load()
            usage = UsageStore(settings.db_path)
            usage.initialize()
            app.state.usage = usage
            app.state.generation = GenerationService(settings, corpus, usage)
        except Exception:
            logging.getLogger("medinote").error("startup_dependencies_unavailable")
        yield
        if app.state.generation:
            await app.state.generation.close()

    app = FastAPI(
        title="MediNote",
        version="1.0",
        openapi_url="/api/openapi.json",
        docs_url=None if settings.env == "production" else "/api/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.bundle = None
    app.state.report = None
    app.state.usage = None
    app.state.generation = None
    app.add_middleware(RequestLimitsMiddleware, origin=settings.public_origin)
    register_error_handlers(app)
    app.include_router(router)

    @app.get("/api/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok", "version": settings.build_sha}

    return app
