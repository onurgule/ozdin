from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").strip()
    t = re.sub(r"\s+", " ", t)
    return t


def content_hash(book_key: str, normalized_body: str) -> str:
    raw = f"{book_key}::{normalized_body}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
