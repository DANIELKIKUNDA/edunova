import pytest

from app.modules.document_engine.domain.model import DocumentChunk
from app.modules.pedagogy.application.context import ContextBuilder
from app.modules.pedagogy.application.quality import PedagogyQualityGate
from app.modules.pedagogy.domain.model import ContentStatus
from app.shared.domain.errors import ValidationError


def _chunk(id_: str, tokens: int, text: str = "contenu utile") -> DocumentChunk:
    return DocumentChunk(id=id_, section_id="s", start_page=1, end_page=1, text=text, ordinal=1, token_estimate=tokens)


def test_context_builder_keeps_source_provenance():
    bundle = ContextBuilder(max_token_estimate=1000).build(document_id="d1", chunks=[_chunk("c1", 200)])
    assert bundle.source_refs[0].document_id == "d1"
    assert bundle.source_refs[0].chunk_id == "c1"
    assert "SOURCE 1" in bundle.text


def test_context_builder_respects_budget():
    bundle = ContextBuilder(max_token_estimate=500).build(document_id="d1", chunks=[_chunk("c1", 300), _chunk("c2", 300)])
    assert len(bundle.source_refs) == 1
    assert bundle.estimated_tokens == 300


def test_context_builder_clips_oversized_only_chunk():
    bundle = ContextBuilder(max_token_estimate=500).build(document_id="d1", chunks=[_chunk("c1", 900, "x" * 5000)])
    assert bundle.estimated_tokens == 500
    assert len(bundle.text) < 3000


def test_context_builder_rejects_empty_sources():
    with pytest.raises(ValidationError):
        ContextBuilder().build(document_id="d1", chunks=[])


def test_quality_gate_forces_human_review_for_medical_content():
    result = PedagogyQualityGate().assess(source_count=2, body="x" * 300, is_medical=True)
    assert result.status == ContentStatus.REVIEW_REQUIRED
    assert "human_review_required_medical" in result.warnings


def test_quality_gate_never_accepts_unsourced_content():
    with pytest.raises(ValidationError):
        PedagogyQualityGate().assess(source_count=0, body="x" * 300)


def test_quality_gate_can_approve_clean_non_medical_content():
    result = PedagogyQualityGate().assess(source_count=1, body="x" * 300)
    assert result.status == ContentStatus.APPROVED
    assert result.score == 100
