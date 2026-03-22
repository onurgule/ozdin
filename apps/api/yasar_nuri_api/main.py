from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from yasar_nuri_api.api.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from yasar_nuri_api.api.routes.health import router as health_router
from yasar_nuri_api.api.routes.v1 import api_router as v1_router
from yasar_nuri_api.config.settings import get_settings
from yasar_nuri_api.infrastructure.providers.gemini import GeminiEmbeddingProvider, GeminiLLMProvider
from yasar_nuri_api.infrastructure.providers.speech_stub import DeviceSpeechConfigProvider
from yasar_nuri_api.infrastructure.redis_cache import RedisCache, create_redis

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logging.getLogger("uvicorn.error").setLevel(settings.log_level)

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = await create_redis(settings)
    app.state.redis_cache = RedisCache(app.state.redis, index_version=settings.index_version)
    if settings.gemini_api_key:
        app.state.llm_provider = GeminiLLMProvider(settings)
        app.state.embedding_provider = GeminiEmbeddingProvider(settings)
    else:
        app.state.llm_provider = None
        app.state.embedding_provider = None
    app.state.speech_config = DeviceSpeechConfigProvider(settings)

    logger.info("api_started", env=settings.api_env)
    yield
    await engine.dispose()
    await app.state.redis.aclose()
    logger.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="YasarNuri API", lifespan=lifespan)

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(v1_router)
    return app


app = create_app()
