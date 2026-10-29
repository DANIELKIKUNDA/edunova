from __future__ import annotations

import re
from dataclasses import replace
from hashlib import sha256

from app.modules.assistant.domain.model import Citation, SourceChunk

_NUMBER = re.compile(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?(?:\s?(?:%|mg|g|kg|ml|l|mmhg|bpm|°c|mol|mmol))?", re.I)

_SUSPICIOUS = (
    re.compile(r"ignore (all|the|previous|prior) instructions?", re.I),
    re.compile(r"disregard .*instructions?", re.I),
    re.compile(r"system prompt|developer message", re.I),
    re.compile(r"ignore[rz]? les instructions", re.I),
    re.compile(r"révèle .*prompt", re.I),
)

_STOPWORDS = {
    "alors", "avec", "avoir", "cette", "comme", "dans", "des", "donc", "elle", "elles", "entre", "est", "être",
    "fait", "font", "il", "ils", "les", "leur", "leurs", "mais", "nous", "par", "pas", "plus", "pour", "que",
    "qui", "sans", "ses", "son", "sont", "sur", "une", "vous", "votre", "aux", "ces", "cet", "ce", "de", "du",
    "la", "le", "un", "et", "ou", "en", "au", "se", "sa", "si", "on", "ne", "je", "tu", "the", "and", "for",
    "from", "with", "this", "that", "are", "was", "were", "into", "than", "then", "when", "what", "which", "who",
}


def _is_suspicious_line(line: str) -> bool:
    return any(p.search(line) for p in _SUSPICIOUS)


def detect_prompt_injection(chunks: tuple[SourceChunk, ...]) -> tuple[str, ...]:
    flags: list[str] = []
    for chunk in chunks:
        if any(p.search(chunk.text) for p in _SUSPICIOUS):
            flags.append(f"suspicious_source_instruction:{chunk.chunk_id}")
    return tuple(flags)


def sanitize_source_chunks(chunks: tuple[SourceChunk, ...]) -> tuple[SourceChunk, ...]:
    """Remove source-embedded instructions before they ever reach the model.

    The original chunk identity/pages are preserved for citation audit. If a chunk
    consists almost entirely of suspicious instructions, it is excluded.
    """
    sanitized: list[SourceChunk] = []
    for chunk in chunks:
        lines = [line for line in chunk.text.splitlines() if line.strip()]
        if not lines:
            continue
        clean = [line for line in lines if not _is_suspicious_line(line)]
        if not clean:
            continue
        suspicious_ratio = 1.0 - (len(clean) / len(lines))
        if suspicious_ratio >= 0.60:
            continue
        text = "\n".join(clean).strip()
        if text:
            sanitized.append(replace(chunk, text=text))
    return tuple(sanitized)


def _normalized_text_fingerprint(text: str) -> str:
    normalized = " ".join(re.findall(r"[\wÀ-ÿ]+", text.casefold()))[:1600]
    return sha256(normalized.encode()).hexdigest()


def diversify_chunks(chunks: tuple[SourceChunk, ...], *, limit: int = 12) -> tuple[SourceChunk, ...]:
    """Keep high-scoring evidence while avoiding duplicate/near-identical context.

    Adjacent chunks from the same document/page range are useful only when they add
    new text. Exact normalized duplicates are always removed. The policy remains
    deterministic to make cache and tests stable.
    """
    selected: list[SourceChunk] = []
    seen_fingerprints: set[str] = set()
    per_document: dict[str, int] = {}
    for chunk in sorted(chunks, key=lambda c: (-c.score, c.document_id, c.start_page, c.chunk_id)):
        fp = _normalized_text_fingerprint(chunk.text)
        if fp in seen_fingerprints:
            continue
        # Avoid spending the entire budget on one document when cross-document
        # evidence exists, while still allowing enough continuity for one course.
        if per_document.get(chunk.document_id, 0) >= 5:
            continue
        duplicate_page = any(
            s.document_id == chunk.document_id
            and s.start_page == chunk.start_page
            and s.end_page == chunk.end_page
            and _token_overlap(s.text, chunk.text) >= 0.88
            for s in selected
        )
        if duplicate_page:
            continue
        selected.append(chunk)
        seen_fingerprints.add(fp)
        per_document[chunk.document_id] = per_document.get(chunk.document_id, 0) + 1
        if len(selected) >= limit:
            break
    return tuple(selected)



def rerank_chunks(chunks: tuple[SourceChunk, ...], query: str) -> tuple[SourceChunk, ...]:
    """Deterministic second-stage reranker.

    Combines retriever score with lexical query coverage and a small section-title
    boost. It adds no paid AI call and makes FTS/fallback retrieval more stable.
    """
    q_terms = _keywords(query)
    rescored = []
    for chunk in chunks:
        body_terms = _keywords(chunk.text)
        title_terms = _keywords(chunk.section_title or "")
        lexical = (len(q_terms & body_terms) / max(1, len(q_terms))) if q_terms else 0.0
        title = (len(q_terms & title_terms) / max(1, len(q_terms))) if q_terms else 0.0
        score = min(1.0, (0.68 * max(0.0, min(1.0, chunk.score))) + (0.24 * lexical) + (0.08 * title))
        rescored.append(replace(chunk, score=round(score, 6)))
    return tuple(sorted(rescored, key=lambda c: (-c.score, c.document_id, c.start_page, c.chunk_id)))


def build_context(chunks: tuple[SourceChunk, ...], *, max_tokens: int, query: str | None = None) -> tuple[str, tuple[SourceChunk, ...]]:
    # ~4 chars/token conservative enough for the pilot. Never exceed source budget.
    budget_chars = max(800, max_tokens * 4)
    sanitized = sanitize_source_chunks(chunks)
    ranked = rerank_chunks(sanitized, query) if query else sanitized
    candidates = diversify_chunks(ranked, limit=16)
    selected: list[SourceChunk] = []
    blocks: list[str] = []
    used = 0
    for chunk in candidates:
        text = " ".join(chunk.text.split())
        block = f'<source id="{chunk.chunk_id}" pages="{chunk.start_page}-{chunk.end_page}">\n{text}\n</source>'
        if selected and used + len(block) > budget_chars:
            continue
        if len(block) > budget_chars and not selected:
            block = block[:budget_chars]
        blocks.append(block)
        selected.append(chunk)
        used += len(block)
        if used >= budget_chars:
            break
    return "\n\n".join(blocks), tuple(selected)


def citations_for(chunks: tuple[SourceChunk, ...], *, limit: int = 5) -> tuple[Citation, ...]:
    out = []
    for c in chunks[:limit]:
        excerpt = " ".join(c.text.split())[:260]
        out.append(Citation(chunk_id=c.chunk_id,document_id=c.document_id,section_title=c.section_title,start_page=c.start_page,end_page=c.end_page,excerpt=excerpt))
    return tuple(out)


def evidence_confidence(chunks: tuple[SourceChunk, ...]) -> float:
    if not chunks:
        return 0.0
    top = sorted((max(0.0, min(1.0, c.score)) for c in chunks), reverse=True)[:3]
    base = sum(top) / len(top)
    diversity = min(0.15, 0.05 * max(0, len({c.document_id for c in chunks}) - 1))
    return round(min(0.98, base + diversity), 3)


def _keywords(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-zà-ÿ0-9]+", text.casefold())
        if len(token) >= 4 and token not in _STOPWORDS and not token.isdigit()
    }


def _token_overlap(left: str, right: str) -> float:
    a, b = _keywords(left), _keywords(right)
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, min(len(a), len(b)))


def grounding_coverage(answer: str, question: str, chunks: tuple[SourceChunk, ...]) -> float:
    """Conservative lexical support indicator used as a post-generation safety gate.

    It is not a truth score. It detects answers drifting away from the supplied
    evidence. Question terms are accepted because the response may legitimately
    repeat user-provided concepts that are not literal in every chunk.
    """
    answer_terms = _keywords(answer)
    if not answer_terms:
        return 1.0
    supported = _keywords(question)
    for chunk in chunks:
        supported.update(_keywords(chunk.text))
    return round(len(answer_terms & supported) / max(1, len(answer_terms)), 3)


def evidence_conflicts(chunks: tuple[SourceChunk, ...]) -> tuple[str, ...]:
    """Surface obvious numeric-unit disagreements as review flags, never as proof.

    This deliberately only considers explicit units to reduce false positives.
    """
    by_unit: dict[str, set[str]] = {}
    for chunk in chunks:
        for match in _NUMBER.finditer(chunk.text.casefold()):
            raw = match.group(0).replace(" ", "").replace(",", ".")
            unit_match = re.search(r"(%|mg|kg|ml|mmhg|bpm|°c|mmol|mol|g|l)$", raw)
            if not unit_match:
                continue
            unit = unit_match.group(1)
            by_unit.setdefault(unit, set()).add(raw)
    flags = []
    for unit, values in sorted(by_unit.items()):
        if 1 < len(values) <= 4:
            flags.append(f"conflicting_numeric_evidence:{unit}:{','.join(sorted(values))}")
    return tuple(flags[:4])


def unsupported_numeric_claims(answer: str, question: str, chunks: tuple[SourceChunk, ...]) -> tuple[str, ...]:
    """Detect numeric claims introduced by the model that are absent from the question/sources.

    This is intentionally conservative: it is a safety flag, not a mathematical proof of hallucination.
    """
    allowed_text = " ".join([question, *(c.text for c in chunks)]).casefold()
    allowed = {m.group(0).replace(" ", "").replace(",", ".").casefold() for m in _NUMBER.finditer(allowed_text)}
    introduced = []
    for match in _NUMBER.finditer(answer.casefold()):
        value = match.group(0).replace(" ", "").replace(",", ".").casefold()
        if value not in allowed and value not in introduced:
            introduced.append(value)
    return tuple(introduced[:8])
