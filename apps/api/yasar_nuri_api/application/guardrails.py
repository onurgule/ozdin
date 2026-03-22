from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from yasar_nuri_api.api.schemas import ChatAskResponse, CitationPayload, EvidenceChunk


@dataclass(frozen=True)
class FallbackCopy:
    insufficient_evidence: str


def load_fallback_messages(fallback_path: Path) -> FallbackCopy:
    import json

    data = json.loads(fallback_path.read_text(encoding="utf-8"))
    return FallbackCopy(insufficient_evidence=str(data["insufficient_evidence"]))


def coerce_insufficient_response(fallback: FallbackCopy) -> ChatAskResponse:
    return ChatAskResponse(
        answer=fallback.insufficient_evidence,
        found=False,
        confidence=0.0,
        citations=[],
        disclaimer=None,
    )


def validate_and_merge_citations(
    raw: ChatAskResponse,
    evidence_by_id: dict[UUID, EvidenceChunk],
    *,
    fallback: FallbackCopy,
    min_confidence: float,
) -> ChatAskResponse:
    if not raw.found:
        return coerce_insufficient_response(fallback)
    if raw.confidence < min_confidence:
        return coerce_insufficient_response(fallback)

    fixed_citations: list[CitationPayload] = []
    for c in raw.citations:
        try:
            cid = UUID(c.chunk_id)
        except ValueError:
            continue
        ev = evidence_by_id.get(cid)
        if ev is None:
            continue
        fixed_citations.append(
            CitationPayload(
                chunk_id=str(ev.id),
                book_title=ev.book_title,
                section_title=ev.section_title,
                page_number=ev.page_number,
                surah_name=ev.surah_name,
                ayah_start=ev.ayah_start,
                ayah_end=ev.ayah_end,
                question_text=ev.question_text,
            )
        )

    if raw.found and not fixed_citations:
        return coerce_insufficient_response(fallback)

    conf = min(raw.confidence, 0.95 if fixed_citations else 0.0)
    return ChatAskResponse(
        answer=raw.answer,
        found=True,
        confidence=conf,
        citations=fixed_citations,
        disclaimer=raw.disclaimer,
    )
