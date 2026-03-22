from __future__ import annotations

MAX_CHARS = 1800


def split_long_text(text: str, *, max_chars: int = MAX_CHARS) -> list[str]:
    t = text.strip()
    if len(t) <= max_chars:
        return [t]
    parts: list[str] = []
    start = 0
    while start < len(t):
        end = min(start + max_chars, len(t))
        chunk = t[start:end]
        parts.append(chunk.strip())
        start = end
    return [p for p in parts if p]
