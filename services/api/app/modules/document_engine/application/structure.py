from __future__ import annotations

import re
import uuid

from ..domain.model import DocumentSection, ExtractedPage, TextSpan
from ..infrastructure.pdf import dominant_font_size

_NUMBERED = re.compile(r"^(?:(?:chapitre|chapter|partie|section)\s+)?(?:[IVXLCDM]+|\d+(?:\.\d+){0,3})[\s.\-:]+.+$", re.IGNORECASE)
_SHORT = 110


def build_sections(pages: tuple[ExtractedPage, ...]) -> tuple[DocumentSection, ...]:
    baseline = dominant_font_size(pages)
    candidates: list[tuple[str, int, int, float]] = []
    seen: set[tuple[str, int]] = set()
    for page in pages:
        for span in page.spans:
            title = " ".join(span.text.split()).strip(" .:-")
            if not _is_heading(span, title, baseline):
                continue
            key = (title.casefold(), page.number)
            if key in seen:
                continue
            seen.add(key)
            level = _level(title, span.font_size, baseline)
            candidates.append((title, page.number, level, span.y0))
    candidates.sort(key=lambda item: (item[1], item[3]))

    if not candidates:
        # Deterministic fallback: one section per page range keeps navigation useful.
        return tuple(
            DocumentSection(
                id=f"sec-{page.number}",
                title=f"Page {page.number}",
                level=1,
                start_page=page.number,
                end_page=page.number,
            )
            for page in pages
            if page.text.strip()
        )

    sections: list[DocumentSection] = []
    parent_stack: list[tuple[int, str]] = []
    for index, (title, start_page, level, _) in enumerate(candidates):
        next_page = candidates[index + 1][1] if index + 1 < len(candidates) else pages[-1].number
        end_page = max(start_page, next_page - (1 if next_page > start_page else 0))
        while parent_stack and parent_stack[-1][0] >= level:
            parent_stack.pop()
        parent_id = parent_stack[-1][1] if parent_stack else None
        section_id = f"sec-{uuid.uuid5(uuid.NAMESPACE_URL, f'{start_page}:{level}:{title}').hex[:14]}"
        sections.append(DocumentSection(section_id, title, level, start_page, end_page, parent_id))
        parent_stack.append((level, section_id))
    return tuple(sections)


def _is_heading(span: TextSpan, title: str, baseline: float) -> bool:
    if not title or len(title) > _SHORT or len(title) < 3:
        return False
    if title.endswith(('.', ',', ';')) and len(title.split()) > 8:
        return False
    words = title.split()
    upper_ratio = sum(1 for c in title if c.isupper()) / max(1, sum(1 for c in title if c.isalpha()))
    numbered = bool(_NUMBERED.match(title))
    large = span.font_size >= baseline * 1.18
    very_large = span.font_size >= baseline * 1.42
    compact = len(words) <= 12
    return very_large or numbered or (compact and large and (span.is_bold or upper_ratio >= 0.55))


def _level(title: str, size: float, baseline: float) -> int:
    match = re.match(r"^(\d+(?:\.\d+){0,3})", title)
    if match:
        return min(4, match.group(1).count('.') + 1)
    lowered = title.lower()
    if lowered.startswith(("chapitre", "chapter", "partie")) or size >= baseline * 1.55:
        return 1
    if size >= baseline * 1.30:
        return 2
    return 3
