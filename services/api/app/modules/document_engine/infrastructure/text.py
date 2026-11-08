from __future__ import annotations

import re
import unicodedata

_HYPHEN_LINE = re.compile(r"(?<=\w)-\s*\n\s*(?=\w)")
_MULTI_SPACE = re.compile(r"[ \t\u00a0]+")
_MANY_NEWLINES = re.compile(r"\n{3,}")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _CONTROL.sub("", value)
    value = _HYPHEN_LINE.sub("", value)
    lines = [_MULTI_SPACE.sub(" ", line).strip() for line in value.split("\n")]
    value = "\n".join(lines)
    value = _MANY_NEWLINES.sub("\n\n", value)
    return value.strip()


def estimate_tokens(text: str) -> int:
    # Conservative language-agnostic estimate suitable for budgeting/chunking.
    return max(1, round(len(text) / 4)) if text else 0


def remove_repeating_page_margins(page_texts: list[str]) -> list[str]:
    """Removes recurring headers/footers from 4+ page documents.

    Page numbers are normalized before frequency analysis. Body lines are never
    removed merely because they repeat unless they occur at a page margin.
    """
    if len(page_texts) < 4:
        return page_texts
    from collections import Counter
    import math

    def signature(line: str) -> str:
        line = line.casefold().strip()
        line = re.sub(r"\b\d+\b", "#", line)
        line = _MULTI_SPACE.sub(" ", line)
        return line

    top = Counter()
    bottom = Counter()
    split_pages: list[list[str]] = []
    for text in page_texts:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        split_pages.append(lines)
        for line in lines[:1]:
            if len(line) <= 140:
                top[signature(line)] += 1
        for line in lines[-1:]:
            if len(line) <= 140:
                bottom[signature(line)] += 1
    threshold = max(3, math.ceil(len(page_texts) * 0.55))
    recurring_top = {value for value, count in top.items() if count >= threshold and value}
    recurring_bottom = {value for value, count in bottom.items() if count >= threshold and value}

    cleaned: list[str] = []
    for lines in split_pages:
        start = 0
        end = len(lines)
        while start < min(1, len(lines)) and signature(lines[start]) in recurring_top:
            start += 1
        while end > max(start, len(lines) - 1) and signature(lines[end - 1]) in recurring_bottom:
            end -= 1
        cleaned.append(normalize_text("\n".join(lines[start:end])))
    return cleaned
