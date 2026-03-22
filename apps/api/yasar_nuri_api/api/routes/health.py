from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.deps import get_db
from yasar_nuri_api.config.settings import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    redis_ok = False
    r = getattr(request.app.state, "redis", None)
    if r is not None:
        try:
            redis_ok = bool(await r.ping())
        except Exception:
            redis_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "redis": redis_ok,
        "index_version": settings.index_version,
    }
