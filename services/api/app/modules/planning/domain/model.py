from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from math import ceil
from typing import Iterable

from app.shared.domain.errors import ValidationError


class AcademicEventKind(StrEnum):
    COURSE = "course"
    INTERROGATION = "interrogation"
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    PRACTICAL = "practical"
    PERSONAL = "personal"


class StudyTaskKind(StrEnum):
    READ = "read"
    SUMMARY = "summary"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    ERRORS = "errors"
    MOCK_EXAM = "mock_exam"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True, slots=True)
class TimetableEntry:
    id: str
    course_id: str
    weekday: int
    start_minute: int
    end_minute: int
    location: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.weekday <= 7:
            raise ValidationError("weekday must be between 1 and 7")
        if not 0 <= self.start_minute < self.end_minute <= 24 * 60:
            raise ValidationError("invalid timetable time range")


@dataclass(frozen=True, slots=True)
class AcademicEvent:
    id: str
    course_id: str | None
    title: str
    kind: AcademicEventKind
    starts_at: datetime
    estimated_minutes: int = 60

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None:
            raise ValidationError("academic event must be timezone-aware")
        if not self.title.strip() or self.estimated_minutes < 1:
            raise ValidationError("invalid academic event")


@dataclass(frozen=True, slots=True)
class CoursePlanningState:
    course_id: str
    readiness: int
    open_errors: int = 0
    due_flashcards: int = 0
    unread_sections: int = 0
    last_studied_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.readiness <= 100:
            raise ValidationError("readiness must be between 0 and 100")
        if min(self.open_errors, self.due_flashcards, self.unread_sections) < 0:
            raise ValidationError("planning counters cannot be negative")
        if self.last_studied_at is not None and self.last_studied_at.tzinfo is None:
            raise ValidationError("last_studied_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class StudyTaskCandidate:
    id: str
    course_id: str
    title: str
    kind: StudyTaskKind
    estimated_minutes: int
    learning_value: float = 0.5
    splittable: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.title.strip() or self.estimated_minutes < 1:
            raise ValidationError("invalid study task candidate")
        if not 0 <= self.learning_value <= 1:
            raise ValidationError("learning_value must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class PrioritizedTask:
    task: StudyTaskCandidate
    priority: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlannedTask:
    id: str
    course_id: str
    title: str
    kind: StudyTaskKind
    minutes: int
    priority: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DayPlan:
    generated_at: datetime
    budget_minutes: int
    tasks: tuple[PlannedTask, ...]

    @property
    def planned_minutes(self) -> int:
        return sum(task.minutes for task in self.tasks)


@dataclass(frozen=True, slots=True)
class NotificationIntent:
    event_id: str
    fire_at: datetime
    title: str
    body: str
    category: str


class ScheduleConflictDetector:
    def find(self, entries: Iterable[TimetableEntry]) -> tuple[tuple[str, str], ...]:
        rows = sorted(entries, key=lambda e: (e.weekday, e.start_minute, e.end_minute, e.id))
        conflicts: list[tuple[str, str]] = []
        for i, left in enumerate(rows):
            for right in rows[i + 1 :]:
                if right.weekday != left.weekday:
                    break
                if right.start_minute >= left.end_minute:
                    break
                if right.start_minute < left.end_minute and left.start_minute < right.end_minute:
                    conflicts.append((left.id, right.id))
        return tuple(conflicts)


class PriorityEngine:
    """Explainable priority score; no opaque ML required."""

    def rank(
        self,
        *,
        now: datetime,
        states: dict[str, CoursePlanningState],
        events: Iterable[AcademicEvent],
        tasks: Iterable[StudyTaskCandidate],
        tomorrow_course_ids: set[str] | None = None,
    ) -> tuple[PrioritizedTask, ...]:
        if now.tzinfo is None:
            raise ValidationError("now must be timezone-aware")
        tomorrow_course_ids = tomorrow_course_ids or set()
        nearest: dict[str, AcademicEvent] = {}
        for event in events:
            if event.course_id is None or event.starts_at < now:
                continue
            current = nearest.get(event.course_id)
            if current is None or event.starts_at < current.starts_at:
                nearest[event.course_id] = event

        ranked: list[PrioritizedTask] = []
        for task in tasks:
            state = states.get(task.course_id, CoursePlanningState(task.course_id, readiness=0))
            score = int(round(task.learning_value * 20))
            reasons: list[str] = []

            event = nearest.get(task.course_id)
            if event is not None:
                hours = max(0.0, (event.starts_at - now).total_seconds() / 3600)
                if hours <= 24:
                    score += 40
                    reasons.append("évaluation dans ≤24 h")
                elif hours <= 72:
                    score += 30
                    reasons.append("évaluation dans ≤3 jours")
                elif hours <= 168:
                    score += 20
                    reasons.append("évaluation dans ≤7 jours")
                elif hours <= 336:
                    score += 10
                    reasons.append("évaluation dans ≤14 jours")

            readiness_gap = 100 - state.readiness
            score += round(readiness_gap * 0.25)
            if state.readiness < 50:
                reasons.append("préparation faible")
            if state.open_errors:
                score += min(18, state.open_errors * 2)
                reasons.append(f"{state.open_errors} erreur(s) à corriger")
            if state.due_flashcards:
                score += min(10, ceil(state.due_flashcards / 3))
                reasons.append("flashcards dues")
            if task.course_id in tomorrow_course_ids:
                score += 8
                reasons.append("cours prévu demain")
            if state.last_studied_at is not None:
                days = max(0, (now - state.last_studied_at).days)
                if days >= 5:
                    score += min(10, days)
                    reasons.append("matière peu revue récemment")

            ranked.append(PrioritizedTask(task=task, priority=min(100, score), reasons=tuple(dict.fromkeys(reasons))))
        return tuple(sorted(ranked, key=lambda row: (-row.priority, row.task.estimated_minutes, row.task.id)))


class TimeBoxPlanner:
    def build(self, *, now: datetime, ranked: Iterable[PrioritizedTask], budget_minutes: int) -> DayPlan:
        if now.tzinfo is None:
            raise ValidationError("now must be timezone-aware")
        if budget_minutes < 5:
            raise ValidationError("budget_minutes must be at least 5")
        remaining = budget_minutes
        tasks: list[PlannedTask] = []
        for row in ranked:
            if remaining < 5:
                break
            requested = row.task.estimated_minutes
            if requested <= remaining:
                minutes = requested
            elif row.task.splittable:
                minutes = remaining
            else:
                continue
            if minutes < 5:
                continue
            tasks.append(PlannedTask(
                id=row.task.id,
                course_id=row.task.course_id,
                title=row.task.title,
                kind=row.task.kind,
                minutes=minutes,
                priority=row.priority,
                reasons=row.reasons,
            ))
            remaining -= minutes
        return DayPlan(generated_at=now, budget_minutes=budget_minutes, tasks=tuple(tasks))


class EmergencyPlanner:
    """Builds a focused plan for an assessment within 36 hours."""

    def build(self, *, now: datetime, event: AcademicEvent, state: CoursePlanningState, budget_minutes: int = 60) -> DayPlan:
        if event.course_id is None:
            raise ValidationError("emergency assessment must be linked to a course")
        hours = (event.starts_at - now).total_seconds() / 3600
        if hours < 0 or hours > 36:
            raise ValidationError("emergency mode is reserved for assessments within 36 hours")
        if budget_minutes < 20:
            raise ValidationError("emergency budget must be at least 20 minutes")

        templates = [
            (StudyTaskKind.DIAGNOSTIC, "Diagnostic rapide", .18),
            (StudyTaskKind.SUMMARY, "Points essentiels", .24),
            (StudyTaskKind.ERRORS, "Revoir mes erreurs", .24 if state.open_errors else .12),
            (StudyTaskKind.QUIZ, "Quiz ciblé", .18),
            (StudyTaskKind.MOCK_EXAM, "Mini examen blanc", .16),
        ]
        tasks: list[PlannedTask] = []
        allocated = 0
        for index, (kind, title, ratio) in enumerate(templates):
            if index == len(templates) - 1:
                minutes = budget_minutes - allocated
            else:
                minutes = max(5, round(budget_minutes * ratio))
            allocated += minutes
            tasks.append(PlannedTask(
                id=f"emergency:{event.id}:{kind.value}", course_id=event.course_id, title=title,
                kind=kind, minutes=minutes, priority=100 - index, reasons=("évaluation imminente",),
            ))
        return DayPlan(generated_at=now, budget_minutes=budget_minutes, tasks=tuple(tasks))


class NotificationPlanner:
    """Local notification intents. Normal flow is capped at two pedagogical reminders/day."""

    def for_event(self, *, now: datetime, event: AcademicEvent, readiness: int) -> tuple[NotificationIntent, ...]:
        if now.tzinfo is None or event.starts_at.tzinfo is None:
            raise ValidationError("notification datetimes must be timezone-aware")
        if event.starts_at <= now:
            return ()
        candidates: list[NotificationIntent] = []
        for delta, category in ((timedelta(days=3), "j-3"), (timedelta(days=1), "j-1"), (timedelta(hours=3), "h-3")):
            fire_at = event.starts_at - delta
            if fire_at <= now:
                continue
            body = f"{event.title} approche. Préparation actuelle : {readiness} %."
            candidates.append(NotificationIntent(event.id, fire_at, event.title, body, category))
        return tuple(candidates)
