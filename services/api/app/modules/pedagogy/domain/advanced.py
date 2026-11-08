from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
import unicodedata
from typing import Iterable

from app.modules.pedagogy.domain.model import ContentStatus, QuizQuestion
from app.shared.domain.errors import ValidationError


class ContentScope(StrEnum):
    PERSONAL = "personal"
    PLATFORM = "platform"


class CognitiveLevel(StrEnum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


@dataclass(frozen=True, slots=True)
class LearningObjective:
    id: str
    course_id: str
    section_id: str | None
    title: str
    cognitive_level: CognitiveLevel
    prerequisite_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.course_id.strip() or not self.title.strip():
            raise ValidationError("learning objective identifiers/title cannot be empty")
        if self.id in self.prerequisite_ids:
            raise ValidationError("learning objective cannot depend on itself")


@dataclass(frozen=True, slots=True)
class MasteryEvidence:
    objective_id: str
    score: float
    weight: float = 1.0
    recency_factor: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValidationError("mastery evidence score must be between 0 and 1")
        if self.weight <= 0:
            raise ValidationError("mastery evidence weight must be > 0")
        if not 0 < self.recency_factor <= 1:
            raise ValidationError("recency_factor must be in (0, 1]")


class MasteryEstimator:
    """Explainable weighted mastery estimator.

    Recency is provided by the caller so the algorithm remains deterministic,
    timezone-neutral and easy to reproduce on device.
    """

    def calculate(self, evidences: Iterable[MasteryEvidence]) -> int:
        rows = list(evidences)
        if not rows:
            raise ValidationError("at least one mastery evidence is required")
        denominator = sum(row.weight * row.recency_factor for row in rows)
        numerator = sum(row.score * row.weight * row.recency_factor for row in rows)
        if denominator <= 0:
            raise ValidationError("invalid mastery denominator")
        return round(numerator / denominator * 100)


@dataclass(frozen=True, slots=True)
class PracticeCandidate:
    question_id: str
    difficulty: int
    mastery: float
    error_count: int = 0
    seen_count: int = 0
    objective_id: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            raise ValidationError("difficulty must be between 1 and 5")
        if not 0 <= self.mastery <= 1:
            raise ValidationError("mastery must be between 0 and 1")
        if self.error_count < 0 or self.seen_count < 0:
            raise ValidationError("practice counters cannot be negative")


class AdaptivePracticeSelector:
    """Deterministically ranks practice questions by pedagogical need.

    Priority combines low mastery, unresolved mistakes, novelty and a small
    difficulty alignment term. Stable sorting makes offline sessions reproducible.
    """

    def rank(self, candidates: Iterable[PracticeCandidate]) -> tuple[PracticeCandidate, ...]:
        rows = list(candidates)

        def score(row: PracticeCandidate) -> tuple[float, str]:
            low_mastery = (1 - row.mastery) * 55
            mistakes = min(row.error_count, 6) * 7
            novelty = 12 if row.seen_count == 0 else max(0, 8 - row.seen_count)
            target_difficulty = 5 - abs(row.difficulty - max(1, min(5, round(1 + (1 - row.mastery) * 4))))
            return (low_mastery + mistakes + novelty + target_difficulty, row.question_id)

        return tuple(sorted(rows, key=lambda row: (-score(row)[0], score(row)[1])))


class ContentVisibilityPolicy:
    """Prevents unreviewed shared AI content from reaching public students."""

    def can_student_view(self, *, scope: ContentScope, status: ContentStatus) -> bool:
        if status == ContentStatus.REJECTED:
            return False
        if scope == ContentScope.PERSONAL:
            return True
        return status == ContentStatus.PUBLISHED


@dataclass(frozen=True, slots=True)
class QuestionQualityReport:
    valid: bool
    warnings: tuple[str, ...]


class QuestionQualityValidator:
    _space = re.compile(r"\s+")

    @classmethod
    def normalize(cls, value: str) -> str:
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        return cls._space.sub(" ", value.casefold().strip())

    def validate(self, question: QuizQuestion) -> QuestionQualityReport:
        warnings: list[str] = []
        normalized_prompt = self.normalize(question.prompt)
        if len(normalized_prompt) < 12:
            warnings.append("prompt_too_short")
        if question.options:
            normalized_options = [self.normalize(option.text) for option in question.options]
            if len(set(normalized_options)) != len(normalized_options):
                warnings.append("duplicate_options")
            if any(not option for option in normalized_options):
                warnings.append("empty_option")
            if any(option == normalized_prompt for option in normalized_options):
                warnings.append("option_duplicates_prompt")
        if question.meta is not None and not question.explanation.strip():
            warnings.append("generated_question_missing_explanation")
        return QuestionQualityReport(valid=not warnings, warnings=tuple(warnings))

    def find_duplicates(self, questions: Iterable[QuizQuestion]) -> tuple[tuple[str, str], ...]:
        seen: dict[str, str] = {}
        duplicates: list[tuple[str, str]] = []
        for question in questions:
            key = self.normalize(question.prompt)
            if key in seen:
                duplicates.append((seen[key], question.id))
            else:
                seen[key] = question.id
        return tuple(duplicates)
