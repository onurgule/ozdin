from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.config.settings import Settings, get_settings


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


async def verify_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if not settings.api_key:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def verify_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    if not settings.admin_reindex_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not settings.admin_key or x_admin_key != settings.admin_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
