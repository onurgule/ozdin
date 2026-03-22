from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.deps import get_db, verify_api_key
from yasar_nuri_api.api.schemas import FeedbackRequest
from yasar_nuri_api.config.settings import Settings, get_settings
from yasar_nuri_api.infrastructure.db.models import FeedbackEvent
from yasar_nuri_api.infrastructure.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/feedback")


@router.post("")
async def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(verify_api_key)],
) -> dict[str, Any]:
    await enforce_rate_limit(request, settings)
    db.add(
        FeedbackEvent(
            session_id=body.session_id,
            message_id=body.message_id,
            rating=body.rating,
            comment=body.comment,
        )
    )
    await db.commit()
    return {"ok": True}
