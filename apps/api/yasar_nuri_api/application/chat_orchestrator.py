from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.schemas import ChatAskRequest, ChatAskResponse
from yasar_nuri_api.application.answer_service import AnswerService
from yasar_nuri_api.application.guardrails import (
    FallbackCopy,
    coerce_insufficient_response,
    load_fallback_messages,
    validate_and_merge_citations,
)
from yasar_nuri_api.application.query_rewrite_service import QueryRewriteService
from yasar_nuri_api.application.retrieval_service import RetrievalService
from yasar_nuri_api.config.settings import Settings
from yasar_nuri_api.domain.language import detect_language_code
from yasar_nuri_api.domain.text_normalize import normalize_question
from yasar_nuri_api.infrastructure.db.models import ChatMessage, ConversationSession
from yasar_nuri_api.infrastructure.providers.base import BaseEmbeddingProvider, BaseLLMProvider
from yasar_nuri_api.infrastructure.redis_cache import RedisCache
from yasar_nuri_api.infrastructure.repositories.chunk_repository import ChunkRepository


class ChatOrchestrator:
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        *,
        llm: BaseLLMProvider | None,
        embedder: BaseEmbeddingProvider | None,
        cache: RedisCache | None,
        fallback: FallbackCopy,
    ) -> None:
        self._settings = settings
        self._session = session
        self._llm = llm
        self._embedder = embedder
        self._cache = cache
        self._fallback = fallback
        self._repo = ChunkRepository(session)

    @classmethod
    def from_app_state(cls, settings: Settings, session: AsyncSession, state: object) -> ChatOrchestrator:
        fallback = load_fallback_messages(settings.prompt_assets_dir / "fallback_messages.tr.json")
        return cls(
            settings,
            session,
            llm=getattr(state, "llm_provider", None),
            embedder=getattr(state, "embedding_provider", None),
            cache=getattr(state, "redis_cache", None),
            fallback=fallback,
        )

    async def ask(self, req: ChatAskRequest) -> tuple[ChatAskResponse, dict[str, Any]]:
        meta: dict[str, Any] = {}
        q = normalize_question(req.question, max_length=self._settings.max_question_length)
        if not q.strip():
            return coerce_insufficient_response(self._fallback), meta

        lang = detect_language_code(q)
        meta["detected_language"] = lang

        rewrite_svc = QueryRewriteService(self._settings, self._llm, self._cache)
        retrieval_query = await rewrite_svc.build_retrieval_query(q, lang)
        meta["retrieval_query"] = retrieval_query

        if not self._embedder:
            return coerce_insufficient_response(self._fallback), meta

        vecs = await self._embedder.embed_texts([retrieval_query], task_type="retrieval_query")
        if not vecs or not vecs[0]:
            return coerce_insufficient_response(self._fallback), meta
        q_emb = vecs[0]

        retr_svc = RetrievalService(self._settings, self._repo, self._llm, self._cache)
        evidence, retr_conf = await retr_svc.retrieve(
            retrieval_query=retrieval_query,
            query_embedding=q_emb,
            original_question=q,
        )
        meta["retrieval_confidence"] = retr_conf
        meta["evidence_count"] = len(evidence)

        if not evidence or retr_conf < self._settings.retrieval_min_confidence:
            resp = await self._maybe_cached_negative(q, lang, req.answer_language)
            await self._persist_conversation(req, resp, meta)
            return resp, meta

        if not self._llm:
            return coerce_insufficient_response(self._fallback), meta

        answer_svc = AnswerService(self._settings, self._llm)
        raw = await answer_svc.generate_answer(
            original_question=q,
            retrieval_query=retrieval_query,
            answer_language=req.answer_language,
            evidence=evidence,
        )
        by_id = {e.id: e for e in evidence}
        validated = validate_and_merge_citations(
            raw,
            by_id,
            fallback=self._fallback,
            min_confidence=self._settings.retrieval_min_confidence,
        )
        await self._cache_answer_if_safe(q, lang, req.answer_language, validated)
        await self._persist_conversation(req, validated, meta)
        return validated, meta

    async def _maybe_cached_negative(self, question: str, lang: str, answer_lang: str) -> ChatAskResponse:
        if not self._cache:
            return coerce_insufficient_response(self._fallback)
        key = hashlib.sha256(f"{lang}|{answer_lang}|{question}".encode()).hexdigest()
        cached = await self._cache.get_json("ans", key)
        if cached and isinstance(cached, dict):
            try:
                return ChatAskResponse.model_validate(cached)
            except Exception:
                pass
        resp = coerce_insufficient_response(self._fallback)
        await self._cache.set_json(
            "ans",
            key,
            resp.model_dump(),
            self._settings.cache_ttl_answer_seconds,
        )
        return resp

    async def _cache_answer_if_safe(self, question: str, lang: str, answer_lang: str, resp: ChatAskResponse) -> None:
        if not self._cache:
            return
        if resp.found:
            return
        key = hashlib.sha256(f"{lang}|{answer_lang}|{question}".encode()).hexdigest()
        await self._cache.set_json(
            "ans",
            key,
            resp.model_dump(),
            self._settings.cache_ttl_answer_seconds,
        )

    async def _persist_conversation(
        self, req: ChatAskRequest, resp: ChatAskResponse, meta: dict[str, Any]
    ) -> None:
        if not req.session_id:
            return
        sid = req.session_id
        existing = await self._session.get(ConversationSession, sid)
        if existing is None:
            self._session.add(ConversationSession(id=sid))
            await self._session.flush()
        self._session.add(ChatMessage(session_id=sid, role="user", content=req.question))
        self._session.add(
            ChatMessage(
                session_id=sid,
                role="assistant",
                content=resp.answer,
                retrieval_debug=meta if self._settings.feature_debug_evidence else None,
            )
        )
        await self._session.commit()
