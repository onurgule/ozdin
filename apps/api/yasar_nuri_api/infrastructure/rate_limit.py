from __future__ import annotations

from fastapi import HTTPException, Request, status

from yasar_nuri_api.config.settings import Settings


def _client_id(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def enforce_rate_limit(request: Request, settings: Settings) -> None:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return
    key = f"rl:{_client_id(request)}"
    try:
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, 60)
        if n > settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla istek. Lütfen bir süre sonra deneyin.",
            )
    except HTTPException:
        raise
    except Exception:
        # Fail open if Redis errors
        return
