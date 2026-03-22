from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: UUID | None = None
    locale: str | None = None
    answer_language: Literal["tr", "ar"] = "tr"


class CitationPayload(BaseModel):
    chunk_id: str
    book_title: str
    section_title: str | None = None
    page_number: int | None = None
    surah_name: str | None = None
    ayah_start: int | None = None
    ayah_end: int | None = None
    question_text: str | None = None


class ChatAskResponse(BaseModel):
    answer: str
    found: bool
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[CitationPayload]
    disclaimer: str | None = None


class QueryRewriteRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QueryRewriteResponse(BaseModel):
    detected_language: str
    retrieval_query: str


class FeedbackRequest(BaseModel):
    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=2000)
    session_id: UUID | None = None
    message_id: UUID | None = None


class SourceSummaryResponse(BaseModel):
    source_id: str
    title: str
    source_type: str
    excerpt: str | None = None


class EvidenceChunk(BaseModel):
    id: UUID
    book_title: str
    title: str
    excerpt: str
    section_title: str | None
    page_number: int | None
    surah_name: str | None
    ayah_start: int | None
    ayah_end: int | None
    question_text: str | None
    answer_text: str | None
