from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.runtime import runtime
from app.modules.analytics.domain.model import AnalyticsSnapshot, CourseAnalyticsSignal

router = APIRouter()



class CourseSignalIn(BaseModel):
    course_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    coverage: float | None = Field(default=None, ge=0, le=1)
    quiz_mastery: float | None = Field(default=None, ge=0, le=1)
    flashcard_mastery: float | None = Field(default=None, ge=0, le=1)
    weakness_recovery: float | None = Field(default=None, ge=0, le=1)
    open_errors: int = Field(default=0, ge=0, le=100000)
    overdue_flashcards: int = Field(default=0, ge=0, le=100000)
    days_to_next_assessment: int | None = Field(default=None, ge=0, le=3650)
    next_assessment_readiness: int | None = Field(default=None, ge=0, le=100)
    study_minutes_7d: int = Field(default=0, ge=0, le=10080)
    plan_adherence_7d: float | None = Field(default=None, ge=0, le=1)
    mastery_delta_7d: float | None = Field(default=None, ge=-1, le=1)


class AnalyticsIn(BaseModel):
    generated_at: datetime
    study_minutes_7d: int = Field(ge=0, le=10080)
    study_minutes_prev_7d: int = Field(ge=0, le=10080)
    quiz_accuracy_7d: float | None = Field(default=None, ge=0, le=1)
    quiz_accuracy_prev_7d: float | None = Field(default=None, ge=0, le=1)
    plan_adherence_7d: float | None = Field(default=None, ge=0, le=1)
    active_days_7d: int = Field(ge=0, le=7)
    streak_days: int = Field(ge=0, le=100000)
    courses: list[CourseSignalIn] = Field(default_factory=list, max_length=250)


def _serialize(report):
    return {
        "momentum": report.momentum.value,
        "evidence": report.evidence.value,
        "study_time": {
            "current": report.study_time.current,
            "previous": report.study_time.previous,
            "delta": report.study_time.delta,
            "direction": report.study_time.direction.value,
        },
        "quiz_accuracy": None if report.quiz_accuracy is None else {
            "current": report.quiz_accuracy.current,
            "previous": report.quiz_accuracy.previous,
            "delta": report.quiz_accuracy.delta,
            "direction": report.quiz_accuracy.direction.value,
        },
        "active_days_7d": report.active_days_7d,
        "streak_days": report.streak_days,
        "plan_adherence_7d": report.plan_adherence_7d,
        "course_insights": [{
            "course_id": x.course_id, "title": x.title, "readiness": x.readiness,
            "risk_level": x.risk_level, "focus_reason": x.focus_reason,
            "mastery_direction": x.mastery_direction.value,
        } for x in report.course_insights],
        "recommendations": [{
            "id": x.id, "kind": x.kind.value, "course_id": x.course_id,
            "course_title": x.course_title, "title": x.title, "reason": x.reason,
            "recommended_minutes": x.recommended_minutes, "priority_score": x.priority_score,
            "deep_link": x.deep_link,
        } for x in report.recommendations],
        "explanation": report.explanation,
    }


@router.post("/analyze")
def analyze(body: AnalyticsIn):
    snapshot = AnalyticsSnapshot(
        generated_at=body.generated_at,
        study_minutes_7d=body.study_minutes_7d,
        study_minutes_prev_7d=body.study_minutes_prev_7d,
        quiz_accuracy_7d=body.quiz_accuracy_7d,
        quiz_accuracy_prev_7d=body.quiz_accuracy_prev_7d,
        plan_adherence_7d=body.plan_adherence_7d,
        active_days_7d=body.active_days_7d,
        streak_days=body.streak_days,
        courses=tuple(CourseAnalyticsSignal(**x.model_dump()) for x in body.courses),
    )
    return _serialize(runtime.analytics.analyze(snapshot))
