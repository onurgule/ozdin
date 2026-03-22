from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from yasar_nuri_api.config.settings import Settings
from yasar_nuri_api.infrastructure.providers.base import BaseEmbeddingProvider, BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiLLMProvider")
        genai.configure(api_key=settings.gemini_api_key)
        self._settings = settings
        self._model_name = settings.gemini_llm_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=20))
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
    ) -> dict[str, Any]:
        model = genai.GenerativeModel(
            self._model_name,
            system_instruction=system_prompt,
        )

        def _call() -> dict[str, Any]:
            resp = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    response_mime_type="application/json",
                ),
            )
            text = (resp.text or "").strip()
            return json.loads(text)

        return await asyncio.to_thread(_call)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=20))
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 512,
    ) -> str:
        model = genai.GenerativeModel(
            self._model_name,
            system_instruction=system_prompt,
        )

        def _call() -> str:
            resp = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            return (resp.text or "").strip()

        return await asyncio.to_thread(_call)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiEmbeddingProvider")
        genai.configure(api_key=settings.gemini_api_key)
        self._settings = settings
        self._model = settings.gemini_embedding_model
        if not self._model.startswith("models/"):
            self._model = f"models/{self._model}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=20))
    async def embed_texts(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        results: list[list[float]] = []

        def _embed_batch(batch: list[str]) -> list[list[float]]:
            out: list[list[float]] = []
            for t in batch:
                tt_map = {
                    "retrieval_query": "RETRIEVAL_QUERY",
                    "retrieval_document": "RETRIEVAL_DOCUMENT",
                }
                tt = tt_map.get(task_type.lower(), task_type)
                r = genai.embed_content(
                    model=self._model,
                    content=t,
                    task_type=tt,
                )
                emb = r.get("embedding")
                if not emb:
                    raise RuntimeError("empty embedding from Gemini")
                out.append(list(emb))
            return out

        # Gemini batch limits — keep small batches
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            part = await asyncio.to_thread(_embed_batch, batch)
            results.extend(part)
        return results
