from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from math import isclose
import re
import unicodedata
from typing import Iterable

from app.shared.domain.errors import ValidationError


class ContentStatus(StrEnum):
    DRAFT_AI = "draft_ai"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class SummaryKind(StrEnum):
    EXPRESS = "express"
    COMPLETE = "complete"
    KEY_POINTS = "key_points"


class QuestionKind(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"
    FREE_TEXT = "free_text"


class ReviewRating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(frozen=True, slots=True)
class SourceRef:
    document_id: str
    chunk_id: str
    start_page: int
    end_page: int
    excerpt: str = ""

    def __post_init__(self) -> None:
        if self.start_page < 1 or self.end_page < self.start_page:
            raise ValidationError("invalid source page range")


@dataclass(frozen=True, slots=True)
class GeneratedContentMeta:
    source_refs: tuple[SourceRef, ...]
    model_id: str | None
    prompt_version: str
    created_at: datetime
    status: ContentStatus = ContentStatus.REVIEW_REQUIRED
    reviewer_id: str | None = None
    source_fingerprint: str | None = None
    generation_key: str | None = None

    def __post_init__(self) -> None:
        if not self.source_refs:
            raise ValidationError("generated content must keep at least one source reference")
        if self.created_at.tzinfo is None:
            raise ValidationError("created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class Summary:
    id: str
    course_id: str
    section_id: str | None
    kind: SummaryKind
    title: str
    body_markdown: str
    estimated_minutes: int
    meta: GeneratedContentMeta

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.body_markdown.strip():
            raise ValidationError("summary content cannot be empty")
        if self.estimated_minutes < 1:
            raise ValidationError("estimated_minutes must be >= 1")


@dataclass(frozen=True, slots=True)
class Flashcard:
    id: str
    course_id: str
    section_id: str | None
    front: str
    back: str
    difficulty: int
    meta: GeneratedContentMeta

    def __post_init__(self) -> None:
        if not self.front.strip() or not self.back.strip():
            raise ValidationError("flashcard front/back cannot be empty")
        if not 1 <= self.difficulty <= 5:
            raise ValidationError("difficulty must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class FlashcardState:
    flashcard_id: str
    repetitions: int = 0
    ease_factor: float = 2.5
    interval_days: int = 0
    due_at: datetime | None = None
    lapses: int = 0

    def __post_init__(self) -> None:
        if self.repetitions < 0 or self.interval_days < 0 or self.lapses < 0:
            raise ValidationError("flashcard state counters cannot be negative")
        if self.ease_factor < 1.3:
            raise ValidationError("ease_factor must be >= 1.3")


@dataclass(frozen=True, slots=True)
class ReviewResult:
    state: FlashcardState
    scheduled_after: timedelta


@dataclass(frozen=True, slots=True)
class QuestionOption:
    id: str
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValidationError("question option text cannot be empty")


@dataclass(frozen=True, slots=True)
class QuizQuestion:
    id: str
    course_id: str
    section_id: str | None
    kind: QuestionKind
    prompt: str
    options: tuple[QuestionOption, ...] = ()
    correct_option_ids: tuple[str, ...] = ()
    expected_numeric: float | None = None
    expected_text: str | None = None
    numeric_tolerance: float = 0.0
    explanation: str = ""
    difficulty: int = 3
    meta: GeneratedContentMeta | None = None
    accepted_text_answers: tuple[str, ...] = ()
    numeric_relative_tolerance: float = 0.0
    learning_objective_id: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValidationError("question prompt cannot be empty")
        if not 1 <= self.difficulty <= 5:
            raise ValidationError("difficulty must be between 1 and 5")
        option_ids = {option.id for option in self.options}
        if len(option_ids) != len(self.options):
            raise ValidationError("question option ids must be unique")
        if self.kind in {QuestionKind.SINGLE_CHOICE, QuestionKind.MULTIPLE_CHOICE, QuestionKind.TRUE_FALSE}:
            if len(self.options) < 2:
                raise ValidationError("choice question needs at least two options")
            if not self.correct_option_ids or not set(self.correct_option_ids).issubset(option_ids):
                raise ValidationError("correct option ids must reference existing options")
            if self.kind in {QuestionKind.SINGLE_CHOICE, QuestionKind.TRUE_FALSE} and len(self.correct_option_ids) != 1:
                raise ValidationError("single/true-false question needs exactly one correct option")
        if self.kind == QuestionKind.NUMERIC and self.expected_numeric is None:
            raise ValidationError("numeric question needs expected_numeric")
        if self.kind == QuestionKind.FREE_TEXT and not (self.expected_text or "").strip():
            raise ValidationError("free text question needs expected_text")
        if self.numeric_tolerance < 0 or self.numeric_relative_tolerance < 0:
            raise ValidationError("numeric tolerances cannot be negative")
        if self.numeric_relative_tolerance > 1:
            raise ValidationError("numeric_relative_tolerance cannot exceed 1")


@dataclass(frozen=True, slots=True)
class Answer:
    selected_option_ids: tuple[str, ...] = ()
    numeric_value: float | None = None
    text_value: str | None = None


@dataclass(frozen=True, slots=True)
class AnswerEvaluation:
    correct: bool
    score: float
    explanation: str

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValidationError("answer score must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class QuizAttemptResult:
    total_questions: int
    correct_questions: int
    score_percent: int
    evaluations: tuple[AnswerEvaluation, ...]


@dataclass(frozen=True, slots=True)
class ErrorItem:
    question_id: str
    first_failed_at: datetime
    last_failed_at: datetime
    failure_count: int = 1
    recovery_streak: int = 0
    recovered_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.failure_count < 1 or self.recovery_streak < 0:
            raise ValidationError("invalid error item counters")


@dataclass(frozen=True, slots=True)
class PreparationSignals:
    coverage: float | None = None
    quiz_mastery: float | None = None
    flashcard_mastery: float | None = None
    weakness_recovery: float | None = None

    def values(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for name in ("coverage", "quiz_mastery", "flashcard_mastery", "weakness_recovery"):
            value = getattr(self, name)
            if value is None:
                continue
            if not 0 <= value <= 1:
                raise ValidationError(f"{name} must be between 0 and 1")
            values[name] = value
        if not values:
            raise ValidationError("at least one preparation signal is required")
        return values


class FlashcardScheduler:
    """Small deterministic scheduler inspired by SM-2.

    It is intentionally explainable and offline-friendly. We can replace the
    implementation later without changing the domain port exposed to the app.
    """

    def review(self, state: FlashcardState, rating: ReviewRating, *, now: datetime | None = None) -> ReviewResult:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValidationError("now must be timezone-aware")

        repetitions = state.repetitions
        ease = state.ease_factor
        lapses = state.lapses

        if rating == ReviewRating.AGAIN:
            interval = 1
            repetitions = 0
            lapses += 1
            ease = max(1.3, ease - 0.20)
        elif rating == ReviewRating.HARD:
            interval = 1 if state.interval_days == 0 else max(1, round(state.interval_days * 1.2))
            repetitions += 1
            ease = max(1.3, ease - 0.15)
        elif rating == ReviewRating.GOOD:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 3
            else:
                interval = max(1, round(max(1, state.interval_days) * ease))
            repetitions += 1
        else:  # EASY
            if repetitions == 0:
                interval = 3
            elif repetitions == 1:
                interval = 7
            else:
                interval = max(2, round(max(1, state.interval_days) * ease * 1.3))
            repetitions += 1
            ease = min(3.2, ease + 0.15)

        due_at = now + timedelta(days=interval)
        new_state = FlashcardState(
            flashcard_id=state.flashcard_id,
            repetitions=repetitions,
            ease_factor=round(ease, 3),
            interval_days=interval,
            due_at=due_at,
            lapses=lapses,
        )
        return ReviewResult(state=new_state, scheduled_after=timedelta(days=interval))


class QuizEvaluator:
    def evaluate(self, question: QuizQuestion, answer: Answer) -> AnswerEvaluation:
        if question.kind in {QuestionKind.SINGLE_CHOICE, QuestionKind.TRUE_FALSE}:
            correct = tuple(answer.selected_option_ids) == tuple(question.correct_option_ids)
            score = 1.0 if correct else 0.0
        elif question.kind == QuestionKind.MULTIPLE_CHOICE:
            expected = set(question.correct_option_ids)
            actual = set(answer.selected_option_ids)
            if not expected and not actual:
                score = 1.0
            else:
                true_positive = len(expected & actual)
                false_positive = len(actual - expected)
                false_negative = len(expected - actual)
                denominator = len(expected | actual) or 1
                score = max(0.0, (true_positive - 0.25 * false_positive - 0.25 * false_negative) / max(1, len(expected)))
            correct = score >= 0.999
        elif question.kind == QuestionKind.NUMERIC:
            if answer.numeric_value is None:
                score, correct = 0.0, False
            else:
                correct = isclose(
                    answer.numeric_value,
                    question.expected_numeric or 0.0,
                    abs_tol=question.numeric_tolerance,
                    rel_tol=question.numeric_relative_tolerance,
                )
                score = 1.0 if correct else 0.0
        else:
            def normalize(value: str) -> str:
                decomposed = unicodedata.normalize("NFKD", value)
                without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
                return re.sub(r"\s+", " ", without_marks.strip().casefold())

            accepted = {normalize(question.expected_text or "")}
            accepted.update(normalize(value) for value in question.accepted_text_answers)
            accepted.discard("")
            actual = normalize(answer.text_value or "")
            correct = bool(actual) and actual in accepted
            score = 1.0 if correct else 0.0
        return AnswerEvaluation(correct=correct, score=round(score, 4), explanation=question.explanation)

    def attempt(self, questions: Iterable[QuizQuestion], answers: Iterable[Answer]) -> QuizAttemptResult:
        question_list = list(questions)
        answer_list = list(answers)
        if len(question_list) != len(answer_list):
            raise ValidationError("questions and answers length must match")
        evaluations = tuple(self.evaluate(question, answer) for question, answer in zip(question_list, answer_list))
        correct = sum(1 for result in evaluations if result.correct)
        raw_score = sum(result.score for result in evaluations)
        percent = 0 if not evaluations else round(raw_score / len(evaluations) * 100)
        return QuizAttemptResult(
            total_questions=len(evaluations),
            correct_questions=correct,
            score_percent=percent,
            evaluations=evaluations,
        )


class ErrorLedger:
    """Keeps mistakes actionable without treating one lucky answer as recovery."""

    RECOVERY_STREAK_REQUIRED = 2

    def fail(self, item: ErrorItem | None, *, question_id: str, at: datetime) -> ErrorItem:
        if item is None:
            return ErrorItem(question_id=question_id, first_failed_at=at, last_failed_at=at)
        return ErrorItem(
            question_id=item.question_id,
            first_failed_at=item.first_failed_at,
            last_failed_at=at,
            failure_count=item.failure_count + 1,
            recovery_streak=0,
            recovered_at=None,
        )

    def succeed(self, item: ErrorItem, *, at: datetime) -> ErrorItem:
        streak = item.recovery_streak + 1
        recovered_at = at if streak >= self.RECOVERY_STREAK_REQUIRED else None
        return ErrorItem(
            question_id=item.question_id,
            first_failed_at=item.first_failed_at,
            last_failed_at=item.last_failed_at,
            failure_count=item.failure_count,
            recovery_streak=streak,
            recovered_at=recovered_at,
        )


class AdaptiveReadinessCalculator:
    """Preparation score that re-normalizes weights when a signal is absent."""

    BASE_WEIGHTS = {
        "coverage": 0.30,
        "quiz_mastery": 0.40,
        "flashcard_mastery": 0.15,
        "weakness_recovery": 0.15,
    }

    def calculate(self, signals: PreparationSignals) -> int:
        values = signals.values()
        weight_sum = sum(self.BASE_WEIGHTS[name] for name in values)
        weighted = sum(values[name] * self.BASE_WEIGHTS[name] for name in values)
        return round(weighted / weight_sum * 100)
