from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from yasar_nuri_api.api.deps import verify_api_key
from yasar_nuri_api.api.schemas import QueryRewriteRequest, QueryRewriteResponse
from yasar_nuri_api.application.query_rewrite_service import QueryRewriteService
from yasar_nuri_api.config.settings import Settings, get_settings
from yasar_nuri_api.domain.language import detect_language_code
from yasar_nuri_api.domain.text_normalize import normalize_question
from yasar_nuri_api.infrastructure.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/query")


@router.post("/rewrite", response_model=QueryRewriteResponse)
async def rewrite_query(
    request: Request,
    body: QueryRewriteRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[None, Depends(verify_api_key)],
) -> QueryRewriteResponse:
    await enforce_rate_limit(request, settings)
    q = normalize_question(body.question, max_length=settings.max_question_length)
    lang = detect_language_code(q)
    svc = QueryRewriteService(
        settings,
        getattr(request.app.state, "llm_provider", None),
        getattr(request.app.state, "redis_cache", None),
    )
    rq = await svc.build_retrieval_query(q, lang)
    return QueryRewriteResponse(detected_language=lang, retrieval_query=rq)
