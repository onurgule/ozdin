from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = _REPO_ROOT / "apps" / "api"
if _API_ROOT.is_dir() and str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from yasar_nuri_api.infrastructure.db.models import (
    Book,
    IngestionJob,
    IngestionJobStatus,
    SourceChunk,
    SourceDocument,
    SourceType,
)

from source_ingestion_tools.adapters import RawChunk, iter_qa_records, iter_quran_records
from source_ingestion_tools.embeddings import embed_batch


def _sync_database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://yasar:yasar@localhost:5432/yasar_nuri",
    )
    return url.replace("+asyncpg", "+psycopg")


def run_ingest(*, format_name: str, path: Path, book_title_override: str | None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)

    book_title = book_title_override or (
        "Cevap Veriyorum (örnek)" if format_name == "qa" else "Kur'an Çevirisi (örnek)"
    )

    if format_name == "qa":
        records = list(iter_qa_records(path, book_title=book_title))
        st = SourceType.qa_book
    else:
        records = list(iter_quran_records(path, book_title=book_title))
        st = SourceType.quran_translation

    engine = create_engine(_sync_database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)

    index_version = int(os.environ.get("INDEX_VERSION", "1"))
    embed_model = os.environ.get("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

    with SessionLocal() as session:
        job = IngestionJob(
            status=IngestionJobStatus.running,
            source_label=path.name,
            stats={"format": format_name, "rows": len(records)},
        )
        session.add(job)
        session.flush()

        book = Book(
            title=book_title,
            source_type=st,
            edition_notes="ingested",
            is_active=True,
        )
        session.add(book)
        session.flush()

        doc = SourceDocument(book_id=book.id, label=path.name)
        session.add(doc)
        session.flush()

        seen_hashes: set[str] = set()
        inserted = 0
        batch_texts: list[str] = []
        batch_chunks: list[RawChunk] = []

        def flush_batch() -> None:
            nonlocal inserted, batch_texts, batch_chunks
            if not batch_chunks:
                return
            vectors = embed_batch(batch_texts, model=embed_model)
            for rc, vec in zip(batch_chunks, vectors, strict=True):
                session.add(
                    SourceChunk(
                        id=uuid.uuid4(),
                        book_id=book.id,
                        source_document_id=doc.id,
                        source_type=st,
                        title=rc.title,
                        original_text=rc.original_text,
                        normalized_text=rc.normalized_text,
                        fts_document=rc.fts_document,
                        page_number=rc.page_number,
                        section_title=rc.section_title,
                        question_text=rc.question_text,
                        answer_text=rc.answer_text,
                        surah_number=rc.surah_number,
                        surah_name=rc.surah_name,
                        ayah_start=rc.ayah_start,
                        ayah_end=rc.ayah_end,
                        chronology_order=rc.chronology_order,
                        topic_tags=rc.topic_tags,
                        aliases=rc.aliases,
                        content_hash=rc.content_hash,
                        index_version=index_version,
                        embedding=vec,
                    )
                )
                inserted += 1
            batch_texts = []
            batch_chunks = []

        for rc in records:
            if rc.content_hash in seen_hashes:
                continue
            stmt = select(SourceChunk.id).where(
                SourceChunk.book_id == book.id,
                SourceChunk.content_hash == rc.content_hash,
            )
            if session.execute(stmt).scalar_one_or_none():
                continue
            seen_hashes.add(rc.content_hash)
            batch_chunks.append(rc)
            batch_texts.append(rc.normalized_text[:8000])
            if len(batch_chunks) >= 16:
                flush_batch()
        flush_batch()

        job.status = IngestionJobStatus.completed
        job.stats = {"inserted": inserted, "format": format_name}
        session.commit()

    engine.dispose()
