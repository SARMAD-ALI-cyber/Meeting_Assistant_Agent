"""Unit tests for transcript normalization."""

from graph.ingest_utils import normalize_transcript


def test_collapse_whitespace() -> None:
    s, trunc = normalize_transcript("  a   b \n c  ", max_chars=1000)
    assert s == "a b c"
    assert trunc is False


def test_truncation_flag() -> None:
    s, trunc = normalize_transcript("abcdefghij", max_chars=5)
    assert s == "abcde"
    assert trunc is True
