from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from source_ingestion_tools.chunking import split_long_text
from source_ingestion_tools.fts_util import SourceType, build_fts_document
from source_ingestion_tools.normalize import content_hash, normalize_text


@dataclass
class RawChunk:
    title: str
    original_text: str
    normalized_text: str
    page_number: int | None
    section_title: str | None
    question_text: str | None
    answer_text: str | None
    surah_number: int | None
    surah_name: str | None
    ayah_start: int | None
    ayah_end: int | None
    chronology_order: int | None
    topic_tags: list[str]
    aliases: list[str]
    source_type: SourceType
    content_hash: str
    fts_document: str


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def iter_qa_records(path: Path, *, book_title: str) -> Iterator[RawChunk]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = normalize_text(row.get("question", "") or "")
                a = normalize_text(row.get("answer", "") or "")
                topic = row.get("topic") or ""
                page = row.get("page")
                aliases_raw = row.get("aliases") or ""
                aliases = [normalize_text(x) for x in aliases_raw.split("|") if x.strip()]
                tags = [normalize_text(topic)] if topic else []
                body = f"S: {q}\nC: {a}"
                for part_i, part in enumerate(split_long_text(body)):
                    nt = normalize_text(part)
                    h = content_hash(book_title, nt + str(part_i))
                    fts = build_fts_document(
                        normalized_text=nt,
                        question_text=q,
                        answer_text=a,
                        title=book_title,
                        aliases=aliases,
                        topic_tags=tags,
                    )
                    yield RawChunk(
                        title=f"{book_title} — Soru-Cevap",
                        original_text=part,
                        normalized_text=nt,
                        page_number=int(page) if page and str(page).isdigit() else None,
                        section_title=topic or None,
                        question_text=q,
                        answer_text=a,
                        surah_number=None,
                        surah_name=None,
                        ayah_start=None,
                        ayah_end=None,
                        chronology_order=None,
                        topic_tags=tags,
                        aliases=aliases,
                        source_type=SourceType.qa_book,
                        content_hash=h,
                        fts_document=fts,
                    )
        return

    for row in _iter_jsonl(path):
        q = normalize_text(str(row.get("question", "")))
        a = normalize_text(str(row.get("answer", "")))
        topic = str(row.get("topic", "") or "")
        page = row.get("page")
        aliases = [normalize_text(str(x)) for x in (row.get("aliases") or [])]
        tags = [normalize_text(topic)] if topic else []
        body = f"S: {q}\nC: {a}"
        for part_i, part in enumerate(split_long_text(body)):
            nt = normalize_text(part)
            h = content_hash(book_title, nt + str(part_i))
            fts = build_fts_document(
                normalized_text=nt,
                question_text=q,
                answer_text=a,
                title=book_title,
                aliases=aliases,
                topic_tags=tags,
            )
            yield RawChunk(
                title=f"{book_title} — Soru-Cevap",
                original_text=part,
                normalized_text=nt,
                page_number=int(page) if isinstance(page, int) or (page and str(page).isdigit()) else None,
                section_title=topic or None,
                question_text=q,
                answer_text=a,
                surah_number=None,
                surah_name=None,
                ayah_start=None,
                ayah_end=None,
                chronology_order=None,
                topic_tags=tags,
                aliases=aliases,
                source_type=SourceType.qa_book,
                content_hash=h,
                fts_document=fts,
            )


def iter_quran_records(path: Path, *, book_title: str) -> Iterator[RawChunk]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows: list[Any] = list(reader)
    else:
        rows = list(_iter_jsonl(path))
    for row in rows:
        surah = str(row.get("surah", "") or "")
        ayah = row.get("ayah")
        chron = row.get("chronology_order")
        text = normalize_text(str(row.get("text", "")))
        page = row.get("page")
        tags = [normalize_text(str(t)) for t in (row.get("tags") or [])]
        nt = text
        h = content_hash(book_title, f"{surah}:{ayah}:{nt}")
        title = f"{book_title} — {surah} {ayah}"
        fts = build_fts_document(
            normalized_text=nt,
            question_text=None,
            answer_text=None,
            title=title,
            aliases=[],
            topic_tags=tags,
        )
        yield RawChunk(
            title=title,
            original_text=str(row.get("text", "")),
            normalized_text=nt,
            page_number=int(page) if page and str(page).isdigit() else None,
            section_title=surah or None,
            question_text=None,
            answer_text=None,
            surah_number=None,
            surah_name=surah or None,
            ayah_start=int(ayah) if ayah is not None and str(ayah).isdigit() else None,
            ayah_end=int(ayah) if ayah is not None and str(ayah).isdigit() else None,
            chronology_order=int(chron) if chron is not None and str(chron).isdigit() else None,
            topic_tags=tags,
            aliases=[],
            source_type=SourceType.quran_translation,
            content_hash=h,
            fts_document=fts,
        )
