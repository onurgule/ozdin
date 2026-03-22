from __future__ import annotations

import re

from langdetect import LangDetectException, detect


def detect_language_code(text: str) -> str:
    t = (text or "").strip()
    if len(t) < 3:
        return "tr"
    if re.search(r"[\u0600-\u06FF]", t):
        return "ar"
    try:
        code = detect(t)
        return code if code in {"tr", "ar", "en", "de", "fr"} else "tr"
    except LangDetectException:
        return "tr"


def should_rewrite_for_retrieval(lang: str) -> bool:
    return lang != "tr"
