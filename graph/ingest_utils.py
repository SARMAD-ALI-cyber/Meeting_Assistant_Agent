"""Normalize transcript text (ingest node helpers)."""

from __future__ import annotations

import re


def normalize_transcript(text: str, *, max_chars: int) -> tuple[str, bool]:
    """Trim, collapse whitespace, optionally truncate.

    Returns (cleaned_text, was_truncated).
    """
    s = text.strip()
    s = re.sub(r"\s+", " ", s)
    if len(s) <= max_chars:
        return s, False
    return s[:max_chars], True
