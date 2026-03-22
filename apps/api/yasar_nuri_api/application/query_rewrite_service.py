from __future__ import annotations

import json
from pathlib import Path

from yasar_nuri_api.config.settings import Settings
from yasar_nuri_api.domain.language import should_rewrite_for_retrieval
from yasar_nuri_api.infrastructure.prompt_loader import load_text
from yasar_nuri_api.infrastructure.providers.base import BaseLLMProvider
from yasar_nuri_api.infrastructure.redis_cache import RedisCache, cache_key_question


class QueryRewriteService:
    def __init__(
        self,
        settings: Settings,
        llm: BaseLLMProvider | None,
        cache: RedisCache | None,
    ) -> None:
        self._settings = settings
        self._llm = llm
        self._cache = cache
        self._system = load_text(Path(settings.prompt_assets_dir) / "system_prompt_query_rewrite.txt")

    async def build_retrieval_query(self, question: str, detected_lang: str) -> str:
        if not should_rewrite_for_retrieval(detected_lang):
            return question
        key = cache_key_question(question, detected_lang)
        if self._cache:
            cached = await self._cache.get_json("qrewrite", key)
            if isinstance(cached, dict) and "retrieval_query" in cached:
                return str(cached["retrieval_query"])
        if not self._llm:
            return question
        user = json.dumps({"question": question, "source_language": detected_lang}, ensure_ascii=False)
        data = await self._llm.generate_json(self._system, user, temperature=0.1, max_output_tokens=256)
        rq = str(data.get("retrieval_query", question)).strip() or question
        if self._cache:
            await self._cache.set_json(
                "qrewrite",
                key,
                {"retrieval_query": rq},
                self._settings.cache_ttl_rewrite_seconds,
            )
        return rq
