from __future__ import annotations

import re
import uuid

from ..domain.model import DocumentChunk, DocumentSection, ExtractedPage
from ..infrastructure.text import estimate_tokens

_SENTENCE = re.compile(r"(?<=[.!?;:])\s+(?=[A-ZÀ-ÖØ-Þ0-9])")


def build_chunks(
    pages: tuple[ExtractedPage, ...],
    sections: tuple[DocumentSection, ...],
    *,
    target_chars: int = 3200,
    overlap_chars: int = 420,
) -> tuple[DocumentChunk, ...]:
    page_map = {page.number: page.text for page in pages}
    ranges = list(sections) or [DocumentSection("root", "Document", 1, 1, pages[-1].number if pages else 1)]
    chunks: list[DocumentChunk] = []
    ordinal = 0
    for section in ranges:
        material: list[tuple[int, str]] = [
            (number, page_map.get(number, ""))
            for number in range(section.start_page, section.end_page + 1)
            if page_map.get(number, "").strip()
        ]
        if not material:
            continue
        buffer = ""
        start_page = material[0][0]
        current_page = start_page
        for page_number, text in material:
            current_page = page_number
            for sentence in _SENTENCE.split(text):
                sentence = sentence.strip()
                if not sentence:
                    continue
                candidate = f"{buffer} {sentence}".strip() if buffer else sentence
                if buffer and len(candidate) > target_chars:
                    ordinal += 1
                    chunks.append(_make_chunk(section.id, start_page, current_page, buffer, ordinal))
                    buffer = buffer[-overlap_chars:].lstrip() + " " + sentence
                    buffer = buffer.strip()
                    start_page = page_number
                else:
                    buffer = candidate
        if buffer:
            ordinal += 1
            chunks.append(_make_chunk(section.id, start_page, current_page, buffer, ordinal))
    return tuple(chunks)


def _make_chunk(section_id: str | None, start_page: int, end_page: int, text: str, ordinal: int) -> DocumentChunk:
    stable = uuid.uuid5(uuid.NAMESPACE_URL, f"{section_id}:{ordinal}:{start_page}:{text[:80]}").hex[:16]
    return DocumentChunk(
        id=f"chunk-{stable}",
        section_id=section_id,
        start_page=start_page,
        end_page=end_page,
        text=text,
        ordinal=ordinal,
        token_estimate=estimate_tokens(text),
    )
