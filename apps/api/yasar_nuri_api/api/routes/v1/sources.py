from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.deps import get_db, verify_api_key
from yasar_nuri_api.api.schemas import SourceSummaryResponse
from yasar_nuri_api.infrastructure.db.models import Book, SourceChunk

router = APIRouter(prefix="/sources")


@router.get("/{source_id}", response_model=SourceSummaryResponse)
async def get_source(
    source_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(verify_api_key)],
) -> SourceSummaryResponse:
    book = await db.get(Book, source_id)
    if book is None or not book.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    stmt = (
        select(SourceChunk.original_text)
        .where(SourceChunk.book_id == book.id)
        .order_by(SourceChunk.created_at.asc())
        .limit(1)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    excerpt = (row[:400] + "…") if row and len(row) > 400 else (row or None)
    return SourceSummaryResponse(
        source_id=str(book.id),
        title=book.title,
        source_type=book.source_type.value,
        excerpt=excerpt,
    )
