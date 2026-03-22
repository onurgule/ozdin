from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from yasar_nuri_api.api.schemas import EvidenceChunk
from yasar_nuri_api.config.settings import Settings
from yasar_nuri_api.domain.rrf import reciprocal_rank_fusion
from yasar_nuri_api.domain.text_normalize import sanitize_fts_query
from yasar_nuri_api.infrastructure.prompt_loader import load_text
from yasar_nuri_api.infrastructure.providers.base import BaseLLMProvider
from yasar_nuri_api.infrastructure.redis_cache import RedisCache, cache_key_question
from yasar_nuri_api.infrastructure.repositories.chunk_repository import ChunkRepository


class RetrievalService:
    def __init__(
        self,
        settings: Settings,
        repo: ChunkRepository,
        llm: BaseLLMProvider | None,
        cache: RedisCache | None,
    ) -> None:
        self._settings = settings
        self._repo = repo
        self._llm = llm
        self._cache = cache
        self._rerank_system = load_text(Path(settings.prompt_assets_dir) / "system_prompt_rerank.txt")

    async def retrieve(
        self,
        *,
        retrieval_query: str,
        query_embedding: list[float],
        original_question: str,
    ) -> tuple[list[EvidenceChunk], float]:
        safe_q = sanitize_fts_query(retrieval_query)
        cache_payload = cache_key_question(safe_q, "retr")
        if self._cache:
            cached = await self._cache.get_json("retr", cache_payload)
            if isinstance(cached, dict) and "ids" in cached:
                ids = [UUID(x) for x in cached["ids"]]
                ev = await self._repo.fetch_evidence(ids)
                conf = float(cached.get("confidence", 0.0))
                return ev, conf

        fts_hits = await self._repo.fts_search(safe_q, limit=self._settings.retrieval_fts_top_k)
        vec_hits = await self._repo.vector_search(query_embedding, limit=self._settings.retrieval_vector_top_k)

        fts_ranked = [cid for cid, _ in fts_hits]
        vec_ranked = [cid for cid, _ in vec_hits]

        merged = reciprocal_rank_fusion([fts_ranked, vec_ranked], k=60)
        top_pairs = merged[: self._settings.retrieval_merged_top_n]
        top_ids = [cid for cid, _ in top_pairs]

        vec_score_by_id = {cid: score for cid, score in vec_hits}
        fts_score_by_id = {cid: score for cid, score in fts_hits}

        confidence = self._blend_confidence(top_ids, vec_score_by_id, fts_score_by_id, top_pairs)

        if self._settings.rerank_enabled and self._llm and top_ids:
            top_ids = await self._rerank_ids(original_question, top_ids)

        evidence = await self._repo.fetch_evidence(top_ids[: self._settings.retrieval_rerank_top_k])

        if self._cache:
            await self._cache.set_json(
                "retr",
                cache_payload,
                {
                    "ids": [str(e.id) for e in evidence],
                    "confidence": confidence,
                },
                self._settings.cache_ttl_retrieval_seconds,
            )

        return evidence, confidence

    def _blend_confidence(
        self,
        top_ids: list[UUID],
        vec_score_by_id: dict[UUID, float],
        fts_score_by_id: dict[UUID, float],
        rrf_pairs: list[tuple[UUID, float]],
    ) -> float:
        if not top_ids:
            return 0.0
        first = top_ids[0]
        vec_part = max(0.0, min(1.0, vec_score_by_id.get(first, 0.0)))
        fts_raw = fts_score_by_id.get(first, 0.0)
        fts_part = max(0.0, min(1.0, fts_raw * 5.0))
        rrf_part = max(0.0, min(1.0, (rrf_pairs[0][1] if rrf_pairs else 0.0) * 40.0))
        return max(0.0, min(1.0, 0.5 * vec_part + 0.25 * fts_part + 0.25 * rrf_part))

    async def _rerank_ids(self, question: str, chunk_ids: list[UUID]) -> list[UUID]:
        chunks = await self._repo.fetch_evidence(chunk_ids)
        by_id = {c.id: c for c in chunks}
        payload = [
            {"chunk_id": str(cid), "excerpt": (by_id[cid].excerpt[:400] if cid in by_id else "")} for cid in chunk_ids
        ]
        user = json.dumps({"question": question, "chunks": payload}, ensure_ascii=False)
        llm = self._llm
        assert llm is not None
        try:
            data = await llm.generate_json(
                self._rerank_system, user, temperature=0.0, max_output_tokens=512
            )
        except Exception:
            return chunk_ids
        ordered = data.get("ordered_chunk_ids")
        if not isinstance(ordered, list):
            return chunk_ids
        out: list[UUID] = []
        seen: set[UUID] = set()
        for x in ordered:
            try:
                u = UUID(str(x))
            except ValueError:
                continue
            if u in seen:
                continue
            if u in by_id:
                seen.add(u)
                out.append(u)
        for cid in chunk_ids:
            if cid not in seen:
                out.append(cid)
        return out
