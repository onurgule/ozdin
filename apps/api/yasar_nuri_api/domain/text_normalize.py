from __future__ import annotations

import re
import unicodedata


def normalize_question(text: str, *, max_length: int) -> str:
    t = unicodedata.normalize("NFKC", text or "").strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) > max_length:
        t = t[:max_length]
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


def sanitize_fts_query(q: str) -> str:
    """Reduce FTS operator injection; keep words."""
    t = unicodedata.normalize("NFKC", q or "").strip()
    t = re.sub(r"[^\w\s\u0600-\u06FF]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:500]
