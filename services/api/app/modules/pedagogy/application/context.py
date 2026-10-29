from __future__ import annotations

from dataclasses import dataclass

from app.modules.document_engine.domain.model import DocumentChunk
from app.modules.pedagogy.domain.model import SourceRef
from app.shared.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class ContextBundle:
    text: str
    source_refs: tuple[SourceRef, ...]
    estimated_tokens: int


class ContextBuilder:
    """Builds a bounded, source-preserving context for RAG/generation."""

    def __init__(self, *, max_token_estimate: int = 6000) -> None:
        if max_token_estimate < 500:
            raise ValidationError("max_token_estimate must be >= 500")
        self.max_token_estimate = max_token_estimate

    def build(self, *, document_id: str, chunks: list[DocumentChunk]) -> ContextBundle:
        if not chunks:
            raise ValidationError("at least one chunk is required")
        selected: list[DocumentChunk] = []
        token_total = 0
        for chunk in chunks:
            if selected and token_total + chunk.token_estimate > self.max_token_estimate:
                break
            if chunk.token_estimate > self.max_token_estimate and not selected:
                # Keep a bounded prefix rather than silently dropping the only source.
                char_budget = self.max_token_estimate * 4
                clipped = chunk.text[:char_budget]
                selected.append(
                    DocumentChunk(
                        id=chunk.id,
                        section_id=chunk.section_id,
                        start_page=chunk.start_page,
                        end_page=chunk.end_page,
                        text=clipped,
                        ordinal=chunk.ordinal,
                        token_estimate=self.max_token_estimate,
                    )
                )
                token_total = self.max_token_estimate
                break
            selected.append(chunk)
            token_total += chunk.token_estimate

        refs = tuple(
            SourceRef(
                document_id=document_id,
                chunk_id=chunk.id,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                excerpt=chunk.text[:280].strip(),
            )
            for chunk in selected
        )
        blocks = [
            f"[SOURCE {idx + 1} | pages {chunk.start_page}-{chunk.end_page} | chunk {chunk.id}]\n{chunk.text.strip()}"
            for idx, chunk in enumerate(selected)
        ]
        return ContextBundle(text="\n\n".join(blocks), source_refs=refs, estimated_tokens=token_total)
