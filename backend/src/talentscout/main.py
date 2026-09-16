"""Application entrypoint: composition root and HTTP wiring."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from talentscout.adapters.claude.client import build_client
from talentscout.adapters.db.session import build_engine, build_session_factory
from talentscout.adapters.security.tokens import TokenService
from talentscout.api.error_handlers import register_error_handlers
from talentscout.api.routers import assessments, auth, candidates, interviews
from talentscout.config import get_settings
from talentscout.logging_config import (
    configure_logging,
    new_correlation_id,
    set_correlation_id,
)

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    engine = build_engine(
        str(settings.database_url),
        echo=settings.debug,
        serverless=settings.serverless,
    )
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.token_service = TokenService(settings.jwt_secret.get_secret_value())
    app.state.claude_client = build_client(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
    )

    logger.info("Started in %s mode using model %s", settings.environment, settings.claude_model)
    try:
        yield
    finally:
        await app.state.claude_client.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="TalentScout",
        description="AI-powered technical screening",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[CORRELATION_ID_HEADER],
    )

    @app.middleware("http")
    async def correlation_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Gives every request a traceable id.

        Logs redact candidate identifiers, so this is how a flow is followed through
        the logs instead.
        """
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or new_correlation_id()
        set_correlation_id(correlation_id)
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response

    register_error_handlers(app)

    for router in (auth.router, candidates.router, interviews.router, assessments.router):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
