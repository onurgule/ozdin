from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from yasar_nuri_api.api.schemas import EvidenceChunk
from yasar_nuri_api.infrastructure.db.models import Book, SourceChunk


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fts_search(self, query: str, *, limit: int) -> list[tuple[UUID, float]]:
        if not query.strip():
            return []
        sql = text(
            """
            SELECT id,
                   ts_rank(
                     to_tsvector('simple', coalesce(fts_document, '')),
                     plainto_tsquery('simple', :q)
                   ) AS rank
            FROM source_chunks
            WHERE to_tsvector('simple', coalesce(fts_document, ''))
                  @@ plainto_tsquery('simple', :q)
            ORDER BY rank DESC
            LIMIT :lim
            """
        )
        result = await self._session.execute(sql, {"q": query, "lim": limit})
        rows = result.mappings().all()
        return [(UUID(str(r["id"])), float(r["rank"] or 0.0)) for r in rows]

    async def vector_search(self, embedding: list[float], *, limit: int) -> list[tuple[UUID, float]]:
        if not embedding:
            return []
        lit = _vector_literal(embedding)
        sql = text(
            """
            SELECT id,
                   1 - (embedding <=> CAST(:emb AS vector)) AS sim
            FROM source_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:emb AS vector)
            LIMIT :lim
            """
        )
        result = await self._session.execute(sql, {"emb": lit, "lim": limit})
        rows = result.mappings().all()
        return [(UUID(str(r["id"])), float(r["sim"] or 0.0)) for r in rows]

    async def fetch_evidence(self, ids: list[UUID]) -> list[EvidenceChunk]:
        if not ids:
            return []
        stmt = select(SourceChunk, Book.title).join(Book, Book.id == SourceChunk.book_id).where(SourceChunk.id.in_(ids))
        result = await self._session.execute(stmt)
        rows = result.all()
        by_id: dict[UUID, tuple[SourceChunk, str]] = {}
        for chunk, book_title in rows:
            by_id[chunk.id] = (chunk, str(book_title))
        out: list[EvidenceChunk] = []
        for i in ids:
            row = by_id.get(i)
            if not row:
                continue
            chunk, book_title = row
            excerpt = (chunk.original_text or "")[:1200]
            out.append(
                EvidenceChunk(
                    id=chunk.id,
                    book_title=book_title,
                    title=chunk.title,
                    excerpt=excerpt,
                    section_title=chunk.section_title,
                    page_number=chunk.page_number,
                    surah_name=chunk.surah_name,
                    ayah_start=chunk.ayah_start,
                    ayah_end=chunk.ayah_end,
                    question_text=chunk.question_text,
                    answer_text=chunk.answer_text,
                )
            )
        return out
