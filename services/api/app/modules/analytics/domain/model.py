from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.shared.domain.errors import ValidationError


class TrendDirection(StrEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class AnalyticsEvidence(StrEnum):
    LIMITED = "limited"
    MODERATE = "moderate"
    STRONG = "strong"


class RecommendationKind(StrEnum):
    ASSESSMENT_FOCUS = "assessment_focus"
    RECOVER_ERRORS = "recover_errors"
    QUIZ_DRILL = "quiz_drill"
    FLASHCARD_REVIEW = "flashcard_review"
    CONTINUE_COURSE = "continue_course"
    PLAN_RECOVERY = "plan_recovery"


@dataclass(frozen=True, slots=True)
class CourseAnalyticsSignal:
    course_id: str
    title: str
    coverage: float | None = None
    quiz_mastery: float | None = None
    flashcard_mastery: float | None = None
    weakness_recovery: float | None = None
    open_errors: int = 0
    overdue_flashcards: int = 0
    days_to_next_assessment: int | None = None
    next_assessment_readiness: int | None = None
    study_minutes_7d: int = 0
    plan_adherence_7d: float | None = None
    mastery_delta_7d: float | None = None

    def __post_init__(self) -> None:
        if not self.course_id.strip() or not self.title.strip():
            raise ValidationError("course identity cannot be empty")
        for name in ("coverage", "quiz_mastery", "flashcard_mastery", "weakness_recovery", "plan_adherence_7d"):
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 1:
                raise ValidationError(f"{name} must be between 0 and 1")
        if self.mastery_delta_7d is not None and not -1 <= self.mastery_delta_7d <= 1:
            raise ValidationError("mastery_delta_7d must be between -1 and 1")
        if self.open_errors < 0 or self.overdue_flashcards < 0 or self.study_minutes_7d < 0:
            raise ValidationError("analytics counters cannot be negative")
        if self.days_to_next_assessment is not None and self.days_to_next_assessment < 0:
            raise ValidationError("days_to_next_assessment cannot be negative")
        if self.next_assessment_readiness is not None and not 0 <= self.next_assessment_readiness <= 100:
            raise ValidationError("next_assessment_readiness must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class AnalyticsSnapshot:
    generated_at: datetime
    study_minutes_7d: int
    study_minutes_prev_7d: int
    quiz_accuracy_7d: float | None
    quiz_accuracy_prev_7d: float | None
    plan_adherence_7d: float | None
    active_days_7d: int
    streak_days: int
    courses: tuple[CourseAnalyticsSignal, ...]

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None:
            raise ValidationError("generated_at must be timezone-aware")
        if self.study_minutes_7d < 0 or self.study_minutes_prev_7d < 0:
            raise ValidationError("study minutes cannot be negative")
        if not 0 <= self.active_days_7d <= 7:
            raise ValidationError("active_days_7d must be between 0 and 7")
        if self.streak_days < 0:
            raise ValidationError("streak_days cannot be negative")
        for name in ("quiz_accuracy_7d", "quiz_accuracy_prev_7d", "plan_adherence_7d"):
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 1:
                raise ValidationError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class TrendMetric:
    current: float
    previous: float
    delta: float
    direction: TrendDirection


@dataclass(frozen=True, slots=True)
class CourseInsight:
    course_id: str
    title: str
    readiness: int | None
    risk_level: str
    focus_reason: str
    mastery_direction: TrendDirection


@dataclass(frozen=True, slots=True)
class StudyRecommendation:
    id: str
    kind: RecommendationKind
    course_id: str | None
    course_title: str | None
    title: str
    reason: str
    recommended_minutes: int
    priority_score: int
    deep_link: str


@dataclass(frozen=True, slots=True)
class AnalyticsReport:
    momentum: TrendDirection
    evidence: AnalyticsEvidence
    study_time: TrendMetric
    quiz_accuracy: TrendMetric | None
    active_days_7d: int
    streak_days: int
    plan_adherence_7d: float | None
    course_insights: tuple[CourseInsight, ...]
    recommendations: tuple[StudyRecommendation, ...]
    explanation: str
