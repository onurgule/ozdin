from __future__ import annotations

import asyncio
import os

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=20))
def embed_batch(texts: list[str], *, model: str) -> list[list[float]]:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY required for ingestion")
    genai.configure(api_key=key)
    m = model if model.startswith("models/") else f"models/{model}"
    out: list[list[float]] = []
    for t in texts:
        r = genai.embed_content(
            model=m,
            content=t,
            task_type="RETRIEVAL_DOCUMENT",
        )
        emb = r.get("embedding")
        if not emb:
            raise RuntimeError("empty embedding")
        out.append(list(emb))
    return out


async def embed_batch_async(texts: list[str], *, model: str) -> list[list[float]]:
    return await asyncio.to_thread(embed_batch, texts, model=model)
