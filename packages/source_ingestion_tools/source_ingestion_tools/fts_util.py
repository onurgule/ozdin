from __future__ import annotations

import re
import unicodedata
from enum import Enum


class SourceType(str, Enum):
    quran_translation = "quran_translation"
    qa_book = "qa_book"


def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").strip()
    t = re.sub(r"\s+", " ", t)
    return t


def build_fts_document(
    *,
    normalized_text: str,
    question_text: str | None,
    answer_text: str | None,
    title: str,
    aliases: list[str],
    topic_tags: list[str],
) -> str:
    parts = [title, normalized_text]
    if question_text:
        parts.append(question_text)
    if answer_text:
        parts.append(answer_text)
    parts.extend(aliases)
    parts.extend(topic_tags)
    return " \n".join(p for p in parts if p)
