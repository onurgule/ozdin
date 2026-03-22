from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio.client import Redis as RedisClient

from yasar_nuri_api.config.settings import Settings


class RedisCache:
    def __init__(self, client: RedisClient, *, index_version: int) -> None:
        self._r = client
        self._index_version = index_version

    def _k(self, kind: str, payload: str) -> str:
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
        return f"v{self._index_version}:{kind}:{h}"

    async def get_json(self, kind: str, payload: str) -> Any | None:
        raw = await self._r.get(self._k(kind, payload))
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, kind: str, payload: str, value: Any, ttl_seconds: int) -> None:
        await self._r.setex(
            self._k(kind, payload),
            ttl_seconds,
            json.dumps(value, ensure_ascii=False),
        )


async def create_redis(settings: Settings) -> RedisClient:
    return redis.from_url(settings.redis_url, decode_responses=True)


def cache_key_question(q: str, lang: str) -> str:
    return f"{lang}::{q}"
