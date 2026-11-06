from __future__ import annotations

import math
import re
from dataclasses import dataclass

from ..domain.model import DocumentChunk

_TOKEN = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk_id: str
    score: float
    start_page: int
    end_page: int
    excerpt: str


def search_chunks(chunks: tuple[DocumentChunk, ...], query: str, *, limit: int = 12) -> tuple[SearchHit, ...]:
    terms = [token.casefold() for token in _TOKEN.findall(query) if len(token) > 1]
    if not terms:
        return ()
    document_frequency = {term: sum(term in _terms(chunk.text) for chunk in chunks) for term in set(terms)}
    total = max(1, len(chunks))
    hits: list[SearchHit] = []
    for chunk in chunks:
        tokens = _terms(chunk.text)
        if not tokens:
            continue
        counts = {term: tokens.count(term) for term in terms}
        if not any(counts.values()):
            continue
        score = 0.0
        for term in terms:
            tf = counts[term] / len(tokens)
            idf = math.log((total + 1) / (document_frequency[term] + 1)) + 1
            score += tf * idf
        if score <= 0:
            continue
        excerpt = _excerpt(chunk.text, terms)
        hits.append(SearchHit(chunk.id, round(score, 6), chunk.start_page, chunk.end_page, excerpt))
    hits.sort(key=lambda item: item.score, reverse=True)
    return tuple(hits[:limit])


def _terms(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN.findall(text)]


def _excerpt(text: str, terms: list[str], radius: int = 130) -> str:
    folded = text.casefold()
    positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
    at = min(positions) if positions else 0
    start = max(0, at - radius)
    end = min(len(text), at + radius * 2)
    prefix = "…" if start else ""
    suffix = "…" if end < len(text) else ""
    return prefix + text[start:end].strip() + suffix
