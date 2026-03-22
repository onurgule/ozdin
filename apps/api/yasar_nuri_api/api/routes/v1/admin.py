from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.deps import get_db, verify_admin
from yasar_nuri_api.config.settings import Settings, get_settings
from yasar_nuri_api.infrastructure.db.models import IngestionJob, IngestionJobStatus

router = APIRouter(prefix="/admin")


@router.post("/reindex")
async def trigger_reindex(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(verify_admin)],
) -> dict[str, Any]:
    job = IngestionJob(
        status=IngestionJobStatus.pending,
        source_label="manual_reindex",
        stats={"note": "Run ingestion CLI on host; job row tracks request"},
    )
    db.add(job)
    await db.commit()
    return {"job_id": str(job.id), "status": job.status.value}
