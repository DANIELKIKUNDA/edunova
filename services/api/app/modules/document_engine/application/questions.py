from __future__ import annotations

import re
import uuid

from ..domain.model import ExtractedPage, QuestionCandidate

_TOP = re.compile(
    r"^\s*(?:(?:question|q)\s*)?(?P<num>\d{1,3}|[IVXLCDM]{1,7})\s*[.)\-:]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
_SUB = re.compile(r"^\s*[a-zA-Z]\s*[.)\-:]\s+.+$")


def extract_question_candidates(pages: tuple[ExtractedPage, ...]) -> tuple[QuestionCandidate, ...]:
    """Extracts numbered questions without using a generative model.

    It deliberately favors precision over recall. Candidates are never published
    automatically; the content pipeline can send them to human validation.
    """
    rows: list[tuple[str, str, int, float]] = []
    current: tuple[str, list[str], int, int] | None = None

    for page in pages:
        for raw_line in page.text.splitlines():
            line = " ".join(raw_line.split()).strip()
            if not line:
                continue
            match = _TOP.match(line)
            if match:
                if current is not None:
                    rows.append(_finalize(*current))
                number = match.group("num")
                body = match.group("body").strip()
                current = (number, [body], page.number, page.number)
                continue
            if current is None:
                continue
            number, parts, start, _ = current
            if _SUB.match(line) or not _looks_like_heading(line):
                parts.append(line)
                current = (number, parts, start, page.number)

    if current is not None:
        rows.append(_finalize(*current))

    candidates: list[QuestionCandidate] = []
    for number, text, start_page, end_page, confidence in rows:
        if len(text) < 8:
            continue
        stable = uuid.uuid5(uuid.NAMESPACE_URL, f"{number}:{start_page}:{text[:120]}").hex[:16]
        candidates.append(
            QuestionCandidate(
                id=f"q-{stable}",
                number_label=number,
                text=text,
                start_page=start_page,
                end_page=end_page,
                confidence=confidence,
            )
        )
    return tuple(candidates)


def _finalize(number: str, parts: list[str], start_page: int, end_page: int):
    text = " ".join(parts).strip()
    confidence = 0.94 if re.fullmatch(r"\d{1,3}", number) else 0.88
    if text.endswith('?'):
        confidence = min(0.99, confidence + 0.03)
    if len(text) > 700:
        confidence -= 0.12
    return number, text, start_page, end_page, round(max(0.0, confidence), 2)


def _looks_like_heading(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    if not letters or len(line) > 120:
        return False
    upper_ratio = sum(c.isupper() for c in letters) / len(letters)
    return upper_ratio > 0.80 and len(line.split()) <= 10
