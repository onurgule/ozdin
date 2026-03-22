from yasar_nuri_api.domain.language import detect_language_code, should_rewrite_for_retrieval
from yasar_nuri_api.domain.text_normalize import normalize_question, sanitize_fts_query


def test_normalize_question_trims() -> None:
    assert normalize_question("  Merhaba   dünya  ", max_length=100) == "Merhaba dünya"


def test_sanitize_fts_query() -> None:
    q = sanitize_fts_query("test & | !")
    assert "|" not in q


def test_detect_arabic_script() -> None:
    assert detect_language_code("ما معنى الصبر") == "ar"


def test_rewrite_flag() -> None:
    assert should_rewrite_for_retrieval("ar") is True
    assert should_rewrite_for_retrieval("tr") is False
