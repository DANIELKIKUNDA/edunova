from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.pedagogy.domain.advanced import AdaptivePracticeSelector, MasteryEstimator, MasteryEvidence, PracticeCandidate
from app.modules.pedagogy.domain.model import (
    AdaptiveReadinessCalculator,
    Answer,
    FlashcardScheduler,
    FlashcardState,
    PreparationSignals,
    QuestionKind,
    QuestionOption,
    QuizEvaluator,
    QuizQuestion,
    ReviewRating,
)

router = APIRouter()


class ReadinessRequest(BaseModel):
    coverage: float | None = Field(default=None, ge=0, le=1)
    quiz_mastery: float | None = Field(default=None, ge=0, le=1)
    flashcard_mastery: float | None = Field(default=None, ge=0, le=1)
    weakness_recovery: float | None = Field(default=None, ge=0, le=1)


class ReviewRequest(BaseModel):
    flashcard_id: str
    rating: Literal["again", "hard", "good", "easy"]
    repetitions: int = 0
    ease_factor: float = 2.5
    interval_days: int = 0
    lapses: int = 0


class MasteryEvidencePayload(BaseModel):
    objective_id: str
    score: float = Field(ge=0, le=1)
    weight: float = Field(default=1, gt=0)
    recency_factor: float = Field(default=1, gt=0, le=1)


class PracticeCandidatePayload(BaseModel):
    question_id: str
    difficulty: int = Field(ge=1, le=5)
    mastery: float = Field(ge=0, le=1)
    error_count: int = Field(default=0, ge=0)
    seen_count: int = Field(default=0, ge=0)
    objective_id: str | None = None


class QuizOptionPayload(BaseModel):
    id: str
    text: str


class QuizEvaluateRequest(BaseModel):
    question_id: str = "preview"
    kind: Literal["single_choice", "multiple_choice", "true_false", "numeric", "free_text"]
    prompt: str
    options: list[QuizOptionPayload] = []
    correct_option_ids: list[str] = []
    expected_numeric: float | None = None
    expected_text: str | None = None
    numeric_tolerance: float = 0.0
    explanation: str = ""
    selected_option_ids: list[str] = []
    numeric_value: float | None = None
    text_value: str | None = None


@router.get("/capabilities")
def capabilities() -> dict:
    return {
        "engine": "edunova-pedagogy",
        "version": "2",
        "features": [
            "adaptive_readiness",
            "flashcard_spaced_repetition",
            "quiz_evaluation",
            "error_ledger",
            "source_bound_generation_contracts",
            "human_review_gate",
            "objective_mastery",
            "adaptive_practice_selection",
            "mixed_question_types",
        ],
    }


@router.post("/readiness")
def readiness(payload: ReadinessRequest) -> dict[str, int]:
    value = AdaptiveReadinessCalculator().calculate(
        PreparationSignals(
            coverage=payload.coverage,
            quiz_mastery=payload.quiz_mastery,
            flashcard_mastery=payload.flashcard_mastery,
            weakness_recovery=payload.weakness_recovery,
        )
    )
    return {"value": value}


@router.post("/flashcards/review")
def review_flashcard(payload: ReviewRequest) -> dict:
    result = FlashcardScheduler().review(
        FlashcardState(
            flashcard_id=payload.flashcard_id,
            repetitions=payload.repetitions,
            ease_factor=payload.ease_factor,
            interval_days=payload.interval_days,
            lapses=payload.lapses,
        ),
        ReviewRating(payload.rating),
        now=datetime.now(timezone.utc),
    )
    state = result.state
    return {
        "flashcard_id": state.flashcard_id,
        "repetitions": state.repetitions,
        "ease_factor": state.ease_factor,
        "interval_days": state.interval_days,
        "due_at": state.due_at.isoformat() if state.due_at else None,
        "lapses": state.lapses,
    }


@router.post("/quiz/evaluate")
def evaluate_quiz(payload: QuizEvaluateRequest) -> dict:
    question = QuizQuestion(
        id=payload.question_id,
        course_id="preview",
        section_id=None,
        kind=QuestionKind(payload.kind),
        prompt=payload.prompt,
        options=tuple(QuestionOption(id=option.id, text=option.text) for option in payload.options),
        correct_option_ids=tuple(payload.correct_option_ids),
        expected_numeric=payload.expected_numeric,
        expected_text=payload.expected_text,
        numeric_tolerance=payload.numeric_tolerance,
        explanation=payload.explanation,
    )
    result = QuizEvaluator().evaluate(
        question,
        Answer(
            selected_option_ids=tuple(payload.selected_option_ids),
            numeric_value=payload.numeric_value,
            text_value=payload.text_value,
        ),
    )
    return {"correct": result.correct, "score": result.score, "explanation": result.explanation}


@router.post("/mastery")
def mastery(payload: list[MasteryEvidencePayload]) -> dict[str, int]:
    value = MasteryEstimator().calculate([
        MasteryEvidence(
            objective_id=row.objective_id, score=row.score, weight=row.weight, recency_factor=row.recency_factor
        ) for row in payload
    ])
    return {"value": value}


@router.post("/practice/rank")
def rank_practice(payload: list[PracticeCandidatePayload]) -> dict[str, list[str]]:
    ranked = AdaptivePracticeSelector().rank([
        PracticeCandidate(
            question_id=row.question_id, difficulty=row.difficulty, mastery=row.mastery,
            error_count=row.error_count, seen_count=row.seen_count, objective_id=row.objective_id,
        ) for row in payload
    ])
    return {"question_ids": [row.question_id for row in ranked]}
