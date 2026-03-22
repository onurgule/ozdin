from pathlib import Path
from uuid import UUID

from yasar_nuri_api.api.schemas import ChatAskResponse, CitationPayload, EvidenceChunk
from yasar_nuri_api.application.guardrails import (
    FallbackCopy,
    coerce_insufficient_response,
    load_fallback_messages,
    validate_and_merge_citations,
)

CID = UUID(int=99)


def test_fallback_exact_sentence(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    p.write_text(
        '{"insufficient_evidence": "Yaşar Nuri Öztürk kaynaklarında bu soruya yeterli dayanak bulunamadı."}',
        encoding="utf-8",
    )
    fb = load_fallback_messages(p)
    r = coerce_insufficient_response(fb)
    assert r.found is False
    assert "Yaşar Nuri Öztürk" in r.answer


def test_citation_strips_unknown_ids() -> None:
    fb = FallbackCopy(insufficient_evidence="x")
    ev = EvidenceChunk(
        id=CID,
        book_title="B",
        title="t",
        excerpt="e",
        section_title=None,
        page_number=3,
        surah_name=None,
        ayah_start=None,
        ayah_end=None,
        question_text=None,
        answer_text=None,
    )
    raw = ChatAskResponse(
        answer="a",
        found=True,
        confidence=0.9,
        citations=[
            CitationPayload(
                chunk_id=str(CID),
                book_title="wrong",
                page_number=999,
            )
        ],
    )
    fixed = validate_and_merge_citations(raw, {CID: ev}, fallback=fb, min_confidence=0.2)
    assert fixed.citations[0].book_title == "B"
    assert fixed.citations[0].page_number == 3


def test_prompt_injection_low_confidence_forces_fallback() -> None:
    fb = FallbackCopy(insufficient_evidence="fallback")
    raw = ChatAskResponse(
        answer="ignore instructions",
        found=True,
        confidence=0.1,
        citations=[],
    )
    out = validate_and_merge_citations(raw, {}, fallback=fb, min_confidence=0.35)
    assert out.answer == "fallback"
