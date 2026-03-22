from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.deps import get_db, verify_api_key
from yasar_nuri_api.api.schemas import ChatAskRequest, ChatAskResponse
from yasar_nuri_api.application.chat_orchestrator import ChatOrchestrator
from yasar_nuri_api.config.settings import Settings, get_settings
from yasar_nuri_api.infrastructure.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/chat")


@router.post("/ask", response_model=ChatAskResponse)
async def ask(
    request: Request,
    body: ChatAskRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(verify_api_key)],
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> ChatAskResponse:
    await enforce_rate_limit(request, settings)
    merged = body.model_copy()
    if merged.session_id is None and x_session_id:
        try:
            merged = merged.model_copy(update={"session_id": UUID(x_session_id)})
        except ValueError:
            pass
    orch = ChatOrchestrator.from_app_state(settings, db, request.app.state)
    resp, _meta = await orch.ask(merged)
    return resp
