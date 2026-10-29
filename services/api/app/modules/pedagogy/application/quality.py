from __future__ import annotations

from dataclasses import dataclass

from app.modules.pedagogy.domain.model import ContentStatus
from app.shared.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class QualityDecision:
    status: ContentStatus
    warnings: tuple[str, ...]
    score: int


class PedagogyQualityGate:
    """Deterministic guardrail before generated content reaches students."""

    def assess(
        self,
        *,
        source_count: int,
        body: str,
        factual_claim_count: int = 0,
        cited_claim_count: int = 0,
        contains_answer_key: bool = False,
        is_medical: bool = False,
    ) -> QualityDecision:
        if source_count < 1:
            raise ValidationError("content without source is forbidden")
        warnings: list[str] = []
        score = 100
        if len(body.strip()) < 80:
            warnings.append("content_too_short")
            score -= 25
        if factual_claim_count > 0 and cited_claim_count < factual_claim_count:
            warnings.append("uncited_claims")
            score -= min(35, (factual_claim_count - cited_claim_count) * 5)
        if contains_answer_key and len(body.strip()) < 150:
            warnings.append("answer_explanation_too_thin")
            score -= 15
        if is_medical:
            warnings.append("human_review_required_medical")
            score = min(score, 89)
        status = ContentStatus.REVIEW_REQUIRED
        if score >= 95 and not is_medical and not warnings:
            status = ContentStatus.APPROVED
        return QualityDecision(status=status, warnings=tuple(warnings), score=max(0, score))
