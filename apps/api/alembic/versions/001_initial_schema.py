"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-03-22

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("quran_translation", "qa_book", name="source_type_enum"),
            nullable=False,
        ),
        sa.Column("edition_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.Column(
            "source_type",
            sa.Enum("quran_translation", "qa_book", name="source_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("fts_document", sa.Text(), server_default="", nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=512), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("surah_number", sa.Integer(), nullable=True),
        sa.Column("surah_name", sa.String(length=256), nullable=True),
        sa.Column("ayah_start", sa.Integer(), nullable=True),
        sa.Column("ayah_end", sa.Integer(), nullable=True),
        sa.Column("chronology_order", sa.Integer(), nullable=True),
        sa.Column("topic_tags", sa.ARRAY(sa.String(length=128)), server_default="{}", nullable=False),
        sa.Column("aliases", sa.ARRAY(sa.String(length=256)), server_default="{}", nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("index_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "content_hash", name="uq_chunk_book_hash"),
    )
    op.create_index("ix_source_chunks_book_id", "source_chunks", ["book_id"])
    op.create_index("ix_source_chunks_content_hash", "source_chunks", ["content_hash"])
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_source_chunks_fts ON source_chunks "
            "USING GIN (to_tsvector('simple', coalesce(fts_document, '')))"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_source_chunks_embedding ON source_chunks "
            "USING hnsw (embedding vector_cosine_ops)"
        )
    )

    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("retrieval_debug", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["conversation_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "feedback_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="ingestion_job_status_enum"),
            nullable=False,
        ),
        sa.Column("source_label", sa.String(length=512), nullable=False),
        sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.execute(sa.text("DROP TYPE IF EXISTS ingestion_job_status_enum"))
    op.drop_table("feedback_events")
    op.drop_table("chat_messages")
    op.drop_table("conversation_sessions")
    op.execute(sa.text("DROP INDEX IF EXISTS ix_source_chunks_embedding"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_source_chunks_fts"))
    op.drop_table("source_chunks")
    op.drop_table("source_documents")
    op.drop_table("books")
    op.execute(sa.text("DROP TYPE IF EXISTS source_type_enum"))
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))
