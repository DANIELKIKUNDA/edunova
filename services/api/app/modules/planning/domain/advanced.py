from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from math import ceil
from typing import Iterable, Mapping

from app.modules.planning.domain.model import StudyTaskKind
from app.shared.domain.errors import ValidationError


class EnergyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssessmentImportance(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def multiplier(self) -> float:
        return {
            AssessmentImportance.LOW: .75,
            AssessmentImportance.NORMAL: 1.0,
            AssessmentImportance.HIGH: 1.2,
            AssessmentImportance.CRITICAL: 1.4,
        }[self]


@dataclass(frozen=True, slots=True)
class AvailabilityWindow:
    id: str
    starts_at: datetime
    ends_at: datetime
    energy: EnergyLevel = EnergyLevel.MEDIUM

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValidationError("availability datetimes must be timezone-aware")
        if self.ends_at <= self.starts_at:
            raise ValidationError("availability window must have positive duration")

    @property
    def minutes(self) -> int:
        return int((self.ends_at - self.starts_at).total_seconds() // 60)


@dataclass(frozen=True, slots=True)
class PlanningConstraints:
    min_block_minutes: int = 5
    max_block_minutes: int = 45
    max_continuous_minutes: int = 50
    break_minutes: int = 10
    max_courses_per_day: int = 4
    max_course_switches: int = 5
    target_readiness: int = 80

    def __post_init__(self) -> None:
        if self.min_block_minutes < 5:
            raise ValidationError("min_block_minutes must be at least 5")
        if self.max_block_minutes < self.min_block_minutes:
            raise ValidationError("max_block_minutes must be >= min_block_minutes")
        if self.max_continuous_minutes < self.min_block_minutes:
            raise ValidationError("max_continuous_minutes must be >= min_block_minutes")
        if self.break_minutes < 0:
            raise ValidationError("break_minutes cannot be negative")
        if self.max_courses_per_day < 1:
            raise ValidationError("max_courses_per_day must be positive")
        if self.max_course_switches < 0:
            raise ValidationError("max_course_switches cannot be negative")
        if not 0 <= self.target_readiness <= 100:
            raise ValidationError("target_readiness must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class AdaptiveCourseState:
    course_id: str
    readiness: int
    readiness_confidence: float = .5
    open_errors: int = 0
    due_flashcards: int = 0
    unread_sections: int = 0
    overdue_minutes: int = 0
    recent_study_minutes: int = 0
    last_studied_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.readiness <= 100:
            raise ValidationError("readiness must be between 0 and 100")
        if not 0 <= self.readiness_confidence <= 1:
            raise ValidationError("readiness_confidence must be between 0 and 1")
        if min(self.open_errors, self.due_flashcards, self.unread_sections, self.overdue_minutes, self.recent_study_minutes) < 0:
            raise ValidationError("planning counters cannot be negative")
        if self.last_studied_at is not None and self.last_studied_at.tzinfo is None:
            raise ValidationError("last_studied_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AdaptiveTaskCandidate:
    id: str
    course_id: str
    title: str
    kind: StudyTaskKind
    remaining_minutes: int
    learning_value: float = .5
    cognitive_load: int = 3
    min_chunk_minutes: int = 5
    max_chunk_minutes: int = 30
    deadline: datetime | None = None
    importance: AssessmentImportance = AssessmentImportance.NORMAL
    prerequisite_task_ids: tuple[str, ...] = ()
    assessment_id: str | None = None
    section_id: str | None = None
    pinned: bool = False
    deferred_count: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.course_id.strip() or not self.title.strip():
            raise ValidationError("invalid adaptive task")
        if self.remaining_minutes < 1:
            raise ValidationError("remaining_minutes must be positive")
        if not 0 <= self.learning_value <= 1:
            raise ValidationError("learning_value must be between 0 and 1")
        if not 1 <= self.cognitive_load <= 5:
            raise ValidationError("cognitive_load must be between 1 and 5")
        if self.min_chunk_minutes < 5 or self.max_chunk_minutes < self.min_chunk_minutes:
            raise ValidationError("invalid task chunk sizes")
        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValidationError("task deadline must be timezone-aware")
        if self.deferred_count < 0:
            raise ValidationError("deferred_count cannot be negative")


@dataclass(frozen=True, slots=True)
class RankedAdaptiveTask:
    task: AdaptiveTaskCandidate
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StudyBlock:
    id: str
    task_id: str
    course_id: str
    title: str
    kind: StudyTaskKind
    starts_at: datetime
    ends_at: datetime
    minutes: int
    priority: int
    reasons: tuple[str, ...]
    window_id: str
    pinned: bool = False


@dataclass(frozen=True, slots=True)
class AdaptiveDayPlan:
    generated_at: datetime
    date: date
    blocks: tuple[StudyBlock, ...]
    available_minutes: int
    study_minutes: int
    break_minutes: int
    warnings: tuple[str, ...] = ()

    @property
    def utilization(self) -> float:
        return 0 if self.available_minutes <= 0 else min(1.0, self.study_minutes / self.available_minutes)


@dataclass(frozen=True, slots=True)
class FeasibilityReport:
    feasible: bool
    required_minutes: int
    available_minutes: int
    deficit_minutes: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HorizonPlan:
    generated_at: datetime
    days: tuple[AdaptiveDayPlan, ...]
    unscheduled_minutes: int
    warnings: tuple[str, ...]


class AdaptivePriorityEngine:
    """Deterministic and explainable priority engine for premium local planning."""

    def rank(
        self,
        *,
        now: datetime,
        states: Mapping[str, AdaptiveCourseState],
        tasks: Iterable[AdaptiveTaskCandidate],
        target_readiness: int = 80,
        completed_task_ids: set[str] | None = None,
    ) -> tuple[RankedAdaptiveTask, ...]:
        if now.tzinfo is None:
            raise ValidationError("now must be timezone-aware")
        completed_task_ids = completed_task_ids or set()
        ranked: list[RankedAdaptiveTask] = []
        for task in tasks:
            if any(dep not in completed_task_ids for dep in task.prerequisite_task_ids):
                continue
            state = states.get(task.course_id, AdaptiveCourseState(task.course_id, readiness=0))
            score = round(task.learning_value * 18)
            reasons: list[str] = []

            if task.pinned:
                score += 100
                reasons.append("tâche épinglée par l’étudiant")

            if task.deadline is not None:
                hours = (task.deadline - now).total_seconds() / 3600
                if hours < 0:
                    score += 45
                    reasons.append("tâche en retard")
                elif hours <= 24:
                    score += round(38 * task.importance.multiplier)
                    reasons.append("échéance dans ≤24 h")
                elif hours <= 72:
                    score += round(30 * task.importance.multiplier)
                    reasons.append("échéance dans ≤3 jours")
                elif hours <= 168:
                    score += round(20 * task.importance.multiplier)
                    reasons.append("échéance dans ≤7 jours")
                elif hours <= 336:
                    score += round(10 * task.importance.multiplier)
                    reasons.append("échéance dans ≤14 jours")

            readiness_gap = max(0, target_readiness - state.readiness)
            score += round(readiness_gap * .35)
            if state.readiness < target_readiness:
                reasons.append(f"préparation sous l’objectif ({state.readiness}/{target_readiness})")

            if state.readiness_confidence < .45 and task.kind in {StudyTaskKind.QUIZ, StudyTaskKind.DIAGNOSTIC, StudyTaskKind.MOCK_EXAM}:
                score += 8
                reasons.append("niveau de maîtrise encore peu fiable")

            if state.open_errors and task.kind == StudyTaskKind.ERRORS:
                score += min(20, state.open_errors * 2)
                reasons.append(f"{state.open_errors} erreur(s) ouvertes")
            if state.due_flashcards and task.kind == StudyTaskKind.FLASHCARDS:
                score += min(14, ceil(state.due_flashcards / 2))
                reasons.append(f"{state.due_flashcards} flashcard(s) dues")
            if state.unread_sections and task.kind in {StudyTaskKind.READ, StudyTaskKind.SUMMARY}:
                score += min(12, state.unread_sections)
                reasons.append("sections du cours non couvertes")
            if state.overdue_minutes:
                score += min(15, ceil(state.overdue_minutes / 10))
                reasons.append("retard de révision à résorber")
            if task.deferred_count:
                score += min(15, task.deferred_count * 4)
                reasons.append(f"reportée {task.deferred_count} fois")
            if state.recent_study_minutes >= 120 and task.kind not in {StudyTaskKind.ERRORS, StudyTaskKind.FLASHCARDS}:
                score -= 8
                reasons.append("matière déjà fortement travaillée récemment")
            if state.last_studied_at is not None:
                days = max(0, (now - state.last_studied_at).days)
                if days >= 5:
                    score += min(10, days)
                    reasons.append("matière peu revue récemment")

            ranked.append(RankedAdaptiveTask(task, max(0, min(200, score)), tuple(dict.fromkeys(reasons))))
        return tuple(sorted(ranked, key=lambda row: (-row.score, row.task.deadline or datetime.max.replace(tzinfo=now.tzinfo), row.task.id)))


class FeasibilityAnalyzer:
    def analyze(
        self,
        *,
        now: datetime,
        deadline: datetime,
        required_minutes: int,
        windows: Iterable[AvailabilityWindow],
    ) -> FeasibilityReport:
        if now.tzinfo is None or deadline.tzinfo is None:
            raise ValidationError("feasibility datetimes must be timezone-aware")
        if required_minutes < 0:
            raise ValidationError("required_minutes cannot be negative")
        available = sum(
            max(0, int((min(w.ends_at, deadline) - max(w.starts_at, now)).total_seconds() // 60))
            for w in windows
            if w.ends_at > now and w.starts_at < deadline
        )
        deficit = max(0, required_minutes - available)
        warnings = () if deficit == 0 else (f"charge irréaliste : déficit de {deficit} min avant l’échéance",)
        return FeasibilityReport(deficit == 0, required_minutes, available, deficit, warnings)


class AdaptiveDayPlanner:
    """Schedules concrete study blocks inside actual availability windows.

    The planner is deterministic, respects fatigue guards, prerequisites, course
    diversity limits and energy/cognitive-load compatibility.
    """

    def __init__(self, priority: AdaptivePriorityEngine | None = None) -> None:
        self.priority = priority or AdaptivePriorityEngine()

    def build(
        self,
        *,
        now: datetime,
        windows: Iterable[AvailabilityWindow],
        states: Mapping[str, AdaptiveCourseState],
        tasks: Iterable[AdaptiveTaskCandidate],
        constraints: PlanningConstraints = PlanningConstraints(),
        completed_task_ids: set[str] | None = None,
    ) -> AdaptiveDayPlan:
        if now.tzinfo is None:
            raise ValidationError("now must be timezone-aware")
        completed_task_ids = set(completed_task_ids or set())
        day_windows = tuple(sorted((w for w in windows if w.ends_at > now), key=lambda w: w.starts_at))
        target_date = day_windows[0].starts_at.date() if day_windows else now.date()
        ranked = list(self.priority.rank(now=now, states=states, tasks=tasks, target_readiness=constraints.target_readiness, completed_task_ids=completed_task_ids))
        remaining = {row.task.id: row.task.remaining_minutes for row in ranked}
        blocks: list[StudyBlock] = []
        warnings: list[str] = []
        courses_used: list[str] = []
        switches = 0
        last_course: str | None = None
        break_total = 0

        for window in day_windows:
            cursor = max(window.starts_at, now)
            continuous = 0
            while cursor < window.ends_at:
                available = int((window.ends_at - cursor).total_seconds() // 60)
                if available < constraints.min_block_minutes:
                    break

                eligible: list[tuple[int, RankedAdaptiveTask]] = []
                for row in ranked:
                    task = row.task
                    if remaining.get(task.id, 0) <= 0:
                        continue
                    if any(dep not in completed_task_ids for dep in task.prerequisite_task_ids):
                        continue
                    if task.course_id not in courses_used and len(set(courses_used)) >= constraints.max_courses_per_day:
                        continue
                    if last_course is not None and task.course_id != last_course and switches >= constraints.max_course_switches:
                        continue
                    if window.energy == EnergyLevel.LOW and task.cognitive_load >= 4:
                        continue
                    energy_bonus = 0
                    if window.energy == EnergyLevel.HIGH and task.cognitive_load >= 4:
                        energy_bonus = 8
                    elif window.energy == EnergyLevel.LOW and task.cognitive_load <= 2:
                        energy_bonus = 5
                    continuity_bonus = 3 if last_course == task.course_id else 0
                    eligible.append((row.score + energy_bonus + continuity_bonus, row))

                if not eligible:
                    break
                eligible.sort(key=lambda item: (-item[0], item[1].task.deadline or datetime.max.replace(tzinfo=now.tzinfo), item[1].task.id))
                _, selected = eligible[0]
                task = selected.task
                max_chunk = min(task.max_chunk_minutes, constraints.max_block_minutes, constraints.max_continuous_minutes - continuous, available, remaining[task.id])
                if max_chunk < task.min_chunk_minutes:
                    if continuous >= constraints.max_continuous_minutes - constraints.min_block_minutes and constraints.break_minutes:
                        shifted = cursor + timedelta(minutes=constraints.break_minutes)
                        if shifted < window.ends_at:
                            cursor = shifted
                            break_total += constraints.break_minutes
                            continuous = 0
                            continue
                    break
                minutes = max_chunk
                end = cursor + timedelta(minutes=minutes)
                block = StudyBlock(
                    id=f"{target_date.isoformat()}:{task.id}:{len(blocks)+1}",
                    task_id=task.id,
                    course_id=task.course_id,
                    title=task.title,
                    kind=task.kind,
                    starts_at=cursor,
                    ends_at=end,
                    minutes=minutes,
                    priority=selected.score,
                    reasons=selected.reasons,
                    window_id=window.id,
                    pinned=task.pinned,
                )
                blocks.append(block)
                remaining[task.id] -= minutes
                if remaining[task.id] <= 0:
                    completed_task_ids.add(task.id)
                if last_course is not None and task.course_id != last_course:
                    switches += 1
                last_course = task.course_id
                courses_used.append(task.course_id)
                cursor = end
                continuous += minutes
                if continuous >= constraints.max_continuous_minutes and constraints.break_minutes:
                    shifted = cursor + timedelta(minutes=constraints.break_minutes)
                    if shifted <= window.ends_at:
                        cursor = shifted
                        break_total += constraints.break_minutes
                    continuous = 0

        available_minutes = sum(max(0, int((w.ends_at - max(w.starts_at, now)).total_seconds() // 60)) for w in day_windows)
        study_minutes = sum(block.minutes for block in blocks)
        unscheduled = sum(remaining.values())
        if not day_windows:
            warnings.append("aucune plage d’étude disponible")
        if unscheduled and study_minutes >= available_minutes * .85 and available_minutes > 0:
            warnings.append("charge supérieure à la capacité disponible aujourd’hui")
        if len(set(courses_used)) >= constraints.max_courses_per_day:
            warnings.append("limite de diversité des matières atteinte")
        return AdaptiveDayPlan(now, target_date, tuple(blocks), available_minutes, study_minutes, break_total, tuple(dict.fromkeys(warnings)))


class HorizonPlanner:
    """Builds a rolling multi-day plan while carrying unfinished work forward."""

    def __init__(self, day_planner: AdaptiveDayPlanner | None = None) -> None:
        self.day_planner = day_planner or AdaptiveDayPlanner()

    def build(
        self,
        *,
        now: datetime,
        windows: Iterable[AvailabilityWindow],
        states: Mapping[str, AdaptiveCourseState],
        tasks: Iterable[AdaptiveTaskCandidate],
        constraints: PlanningConstraints = PlanningConstraints(),
        horizon_days: int = 14,
        completed_task_ids: set[str] | None = None,
    ) -> HorizonPlan:
        if not 1 <= horizon_days <= 60:
            raise ValidationError("horizon_days must be between 1 and 60")
        cutoff = now.date() + timedelta(days=horizon_days - 1)
        windows_by_date: dict[date, list[AvailabilityWindow]] = {}
        for w in windows:
            if now.date() <= w.starts_at.date() <= cutoff:
                windows_by_date.setdefault(w.starts_at.date(), []).append(w)

        remaining = {t.id: t for t in tasks}
        remaining_minutes = {t.id: t.remaining_minutes for t in remaining.values()}
        completed = set(completed_task_ids or set())
        days: list[AdaptiveDayPlan] = []
        cursor_date = now.date()
        while cursor_date <= cutoff:
            day_windows = windows_by_date.get(cursor_date, [])
            day_tasks = [replace(t, remaining_minutes=remaining_minutes[t.id]) for t in remaining.values() if remaining_minutes[t.id] > 0]
            day_now = now if cursor_date == now.date() else datetime.combine(cursor_date, time.min, tzinfo=now.tzinfo)
            plan = self.day_planner.build(now=day_now, windows=day_windows, states=states, tasks=day_tasks, constraints=constraints, completed_task_ids=completed)
            days.append(plan)
            for block in plan.blocks:
                remaining_minutes[block.task_id] = max(0, remaining_minutes[block.task_id] - block.minutes)
                if remaining_minutes[block.task_id] == 0:
                    completed.add(block.task_id)
            cursor_date += timedelta(days=1)

        unscheduled = sum(remaining_minutes.values())
        warnings: list[str] = []
        overdue = [t for t in remaining.values() if remaining_minutes[t.id] > 0 and t.deadline is not None and t.deadline.date() <= cutoff]
        if overdue:
            warnings.append(f"{len(overdue)} tâche(s) risquent de dépasser leur échéance")
        if unscheduled:
            warnings.append(f"{unscheduled} min restent non planifiées sur l’horizon")
        return HorizonPlan(now, tuple(days), unscheduled, tuple(warnings))


class PlanReconciler:
    """Protects user agency and plan stability during replanning."""

    def reconcile(self, *, old_blocks: Iterable[StudyBlock], fresh: AdaptiveDayPlan, completed_block_ids: set[str], pinned_block_ids: set[str]) -> AdaptiveDayPlan:
        old = tuple(old_blocks)
        preserved = [b for b in old if b.id in completed_block_ids or b.id in pinned_block_ids]
        occupied = [(b.starts_at, b.ends_at) for b in preserved]
        fresh_blocks = [
            b for b in fresh.blocks
            if b.id not in {p.id for p in preserved}
            and not any(b.starts_at < end and start < b.ends_at for start, end in occupied)
        ]
        blocks = tuple(sorted((*preserved, *fresh_blocks), key=lambda b: b.starts_at))
        return AdaptiveDayPlan(
            generated_at=fresh.generated_at,
            date=fresh.date,
            blocks=blocks,
            available_minutes=fresh.available_minutes,
            study_minutes=sum(b.minutes for b in blocks),
            break_minutes=fresh.break_minutes,
            warnings=tuple(dict.fromkeys((*fresh.warnings, "plan recalculé en conservant les tâches terminées/épinglées" if preserved else ""))) if preserved else fresh.warnings,
        )


class SmartNotificationPlanner:
    """Optimizes local reminders: quiet hours, deduplication and daily cap."""

    _rank = {"h-3": 30, "j-1": 20, "j-3": 10, "study": 15, "change": 40}

    @staticmethod
    def _minute_of_day(value: datetime) -> int:
        return value.hour * 60 + value.minute

    @staticmethod
    def _in_quiet(minute: int, quiet_start: int, quiet_end: int) -> bool:
        if quiet_start == quiet_end:
            return False
        if quiet_start < quiet_end:
            return quiet_start <= minute < quiet_end
        return minute >= quiet_start or minute < quiet_end

    def optimize(
        self,
        *,
        intents: Iterable,
        event_starts: Mapping[str, datetime],
        quiet_start_minute: int = 22 * 60,
        quiet_end_minute: int = 7 * 60,
        max_per_day: int = 2,
    ) -> tuple:
        if not 0 <= quiet_start_minute < 1440 or not 0 <= quiet_end_minute < 1440:
            raise ValidationError("quiet hour minutes out of range")
        if max_per_day < 1:
            raise ValidationError("max_per_day must be positive")
        adjusted = []
        seen: set[tuple[str, str]] = set()
        for intent in intents:
            key = (intent.event_id, intent.category)
            if key in seen:
                continue
            seen.add(key)
            fire_at = intent.fire_at
            if self._in_quiet(self._minute_of_day(fire_at), quiet_start_minute, quiet_end_minute):
                shifted = fire_at.replace(hour=quiet_end_minute // 60, minute=quiet_end_minute % 60, second=0, microsecond=0)
                if shifted <= fire_at:
                    shifted += timedelta(days=1)
                event_at = event_starts.get(intent.event_id)
                if event_at is not None and shifted >= event_at:
                    continue
                intent = replace(intent, fire_at=shifted)
            adjusted.append(intent)

        by_day: dict[date, list] = {}
        for intent in adjusted:
            by_day.setdefault(intent.fire_at.date(), []).append(intent)
        selected = []
        for day in sorted(by_day):
            rows = sorted(by_day[day], key=lambda i: (-self._rank.get(i.category, 0), i.fire_at, i.event_id))[:max_per_day]
            selected.extend(rows)
        return tuple(sorted(selected, key=lambda i: i.fire_at))

@dataclass(frozen=True, slots=True)
class AssessmentScope:
    event_id: str
    course_id: str
    starts_at: datetime
    section_ids: tuple[str, ...] = ()
    target_readiness: int = 80
    importance: AssessmentImportance = AssessmentImportance.NORMAL
    required_minutes_override: int | None = None

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None:
            raise ValidationError("assessment scope starts_at must be timezone-aware")
        if not 0 <= self.target_readiness <= 100:
            raise ValidationError("target_readiness must be between 0 and 100")
        if self.required_minutes_override is not None and self.required_minutes_override < 0:
            raise ValidationError("required_minutes_override cannot be negative")


@dataclass(frozen=True, slots=True)
class AssessmentPreparation:
    scope: AssessmentScope
    estimated_minutes: int
    tasks: tuple[AdaptiveTaskCandidate, ...]
    reasons: tuple[str, ...]


class AssessmentPreparationFactory:
    """Turns an assessment scope and learning evidence into concrete work.

    The estimate is intentionally transparent and deterministic. It is not a
    prediction of the student's grade.
    """

    def build(self, *, state: AdaptiveCourseState, scope: AssessmentScope) -> AssessmentPreparation:
        if state.course_id != scope.course_id:
            raise ValidationError("assessment scope and state must target the same course")
        gap = max(0, scope.target_readiness - state.readiness)
        read_minutes = min(240, state.unread_sections * 15)
        errors_minutes = min(120, state.open_errors * 4)
        flash_minutes = min(90, max(0, ceil(state.due_flashcards * .8)))
        evidence_minutes = 20 if state.readiness_confidence < .45 else 0
        mastery_minutes = min(120, ceil(gap * 1.5))
        mock_minutes = 30 if scope.importance in {AssessmentImportance.HIGH, AssessmentImportance.CRITICAL} else 20
        estimated = read_minutes + errors_minutes + flash_minutes + evidence_minutes + mastery_minutes + mock_minutes
        if scope.required_minutes_override is not None:
            estimated = scope.required_minutes_override

        reasons: list[str] = []
        if state.unread_sections:
            reasons.append(f"{state.unread_sections} section(s) encore non couvertes")
        if state.open_errors:
            reasons.append(f"{state.open_errors} erreur(s) à récupérer")
        if state.due_flashcards:
            reasons.append(f"{state.due_flashcards} flashcard(s) dues")
        if gap:
            reasons.append(f"écart de préparation de {gap} point(s)")
        if state.readiness_confidence < .45:
            reasons.append("maîtrise à confirmer par diagnostic")

        tasks: list[AdaptiveTaskCandidate] = []
        prerequisite: tuple[str, ...] = ()
        if read_minutes:
            read_id = f"assessment:{scope.event_id}:read"
            tasks.append(AdaptiveTaskCandidate(
                id=read_id,course_id=scope.course_id,title="Couvrir les chapitres au programme",kind=StudyTaskKind.READ,
                remaining_minutes=read_minutes,learning_value=.75,cognitive_load=3,max_chunk_minutes=35,
                deadline=scope.starts_at,importance=scope.importance,assessment_id=scope.event_id,
            ))
            prerequisite = (read_id,)
        if evidence_minutes:
            tasks.append(AdaptiveTaskCandidate(
                id=f"assessment:{scope.event_id}:diagnostic",course_id=scope.course_id,title="Diagnostic de maîtrise",
                kind=StudyTaskKind.DIAGNOSTIC,remaining_minutes=evidence_minutes,learning_value=.95,cognitive_load=4,
                max_chunk_minutes=20,deadline=scope.starts_at,importance=scope.importance,assessment_id=scope.event_id,
                prerequisite_task_ids=prerequisite,
            ))
        if flash_minutes:
            tasks.append(AdaptiveTaskCandidate(
                id=f"assessment:{scope.event_id}:flashcards",course_id=scope.course_id,title="Rappels actifs / flashcards",
                kind=StudyTaskKind.FLASHCARDS,remaining_minutes=flash_minutes,learning_value=.85,cognitive_load=2,
                max_chunk_minutes=20,deadline=scope.starts_at,importance=scope.importance,assessment_id=scope.event_id,
            ))
        if errors_minutes:
            tasks.append(AdaptiveTaskCandidate(
                id=f"assessment:{scope.event_id}:errors",course_id=scope.course_id,title="Corriger les erreurs connues",
                kind=StudyTaskKind.ERRORS,remaining_minutes=errors_minutes,learning_value=1,cognitive_load=4,
                max_chunk_minutes=25,deadline=scope.starts_at,importance=scope.importance,assessment_id=scope.event_id,
            ))
        if mastery_minutes:
            tasks.append(AdaptiveTaskCandidate(
                id=f"assessment:{scope.event_id}:quiz",course_id=scope.course_id,title="Quiz ciblé sur le programme",
                kind=StudyTaskKind.QUIZ,remaining_minutes=mastery_minutes,learning_value=.95,cognitive_load=4,
                max_chunk_minutes=30,deadline=scope.starts_at,importance=scope.importance,assessment_id=scope.event_id,
                prerequisite_task_ids=prerequisite,
            ))
        tasks.append(AdaptiveTaskCandidate(
            id=f"assessment:{scope.event_id}:mock",course_id=scope.course_id,title="Examen blanc / consolidation finale",
            kind=StudyTaskKind.MOCK_EXAM,remaining_minutes=mock_minutes,learning_value=1,cognitive_load=5,
            min_chunk_minutes=20,max_chunk_minutes=30,deadline=scope.starts_at,importance=scope.importance,
            assessment_id=scope.event_id,prerequisite_task_ids=tuple(t.id for t in tasks if t.kind in {StudyTaskKind.READ,StudyTaskKind.DIAGNOSTIC,StudyTaskKind.QUIZ}),
        ))

        if scope.required_minutes_override is not None and tasks:
            minimum_total = 5 * len(tasks)
            if scope.required_minutes_override < minimum_total:
                raise ValidationError(f"required_minutes_override must be at least {minimum_total} for this preparation")
            source_total = sum(t.remaining_minutes for t in tasks)
            target_total = scope.required_minutes_override
            scaled: list[AdaptiveTaskCandidate] = []
            allocated = 0
            for index, task in enumerate(tasks):
                if index == len(tasks) - 1:
                    minutes = target_total - allocated
                else:
                    minutes = max(5, round(task.remaining_minutes / source_total * target_total))
                    max_left_for_this = target_total - allocated - 5 * (len(tasks) - index - 1)
                    minutes = min(minutes, max_left_for_this)
                allocated += minutes
                scaled.append(replace(
                    task, remaining_minutes=minutes, min_chunk_minutes=min(task.min_chunk_minutes, minutes),
                    max_chunk_minutes=max(min(task.max_chunk_minutes, minutes), min(task.min_chunk_minutes, minutes)),
                ))
            tasks = scaled
        return AssessmentPreparation(scope, estimated, tuple(tasks), tuple(reasons))

@dataclass(frozen=True, slots=True)
class BusyInterval:
    id: str
    starts_at: datetime
    ends_at: datetime

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValidationError("busy interval must be timezone-aware")
        if self.ends_at <= self.starts_at:
            raise ValidationError("busy interval must have positive duration")


class AvailabilityDeriver:
    """Subtracts timetable/events from preferred study windows."""

    def derive(self, *, preferred: Iterable[AvailabilityWindow], busy: Iterable[BusyInterval], min_window_minutes: int = 10) -> tuple[AvailabilityWindow, ...]:
        if min_window_minutes < 5:
            raise ValidationError("min_window_minutes must be at least 5")
        busy_rows = sorted(busy, key=lambda b: (b.starts_at, b.ends_at))
        result: list[AvailabilityWindow] = []
        for window in sorted(preferred, key=lambda w: w.starts_at):
            segments = [(window.starts_at, window.ends_at)]
            for item in busy_rows:
                next_segments: list[tuple[datetime,datetime]] = []
                for start, end in segments:
                    if item.ends_at <= start or item.starts_at >= end:
                        next_segments.append((start,end))
                        continue
                    if item.starts_at > start:
                        next_segments.append((start,min(item.starts_at,end)))
                    if item.ends_at < end:
                        next_segments.append((max(item.ends_at,start),end))
                segments = next_segments
            for idx,(start,end) in enumerate(segments):
                if int((end-start).total_seconds()//60) >= min_window_minutes:
                    result.append(AvailabilityWindow(f"{window.id}:free:{idx+1}",start,end,window.energy))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class StudySessionRecord:
    planned_minutes: int
    actual_minutes: int
    completed: bool
    occurred_at: datetime

    def __post_init__(self) -> None:
        if min(self.planned_minutes,self.actual_minutes) < 0:
            raise ValidationError("session minutes cannot be negative")
        if self.occurred_at.tzinfo is None:
            raise ValidationError("session occurred_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AdherenceMetrics:
    planned_minutes: int
    actual_minutes: int
    completed_sessions: int
    total_sessions: int
    time_adherence: float
    completion_rate: float
    suggested_daily_minutes: int
    warning: str | None = None


class AdherenceAnalyzer:
    """Keeps planning humane: learns from what the student actually completes."""

    def analyze(self, *, sessions: Iterable[StudySessionRecord], current_daily_minutes: int) -> AdherenceMetrics:
        rows = tuple(sessions)
        if current_daily_minutes < 5:
            raise ValidationError("current_daily_minutes must be at least 5")
        planned = sum(r.planned_minutes for r in rows)
        actual = sum(r.actual_minutes for r in rows)
        completed = sum(1 for r in rows if r.completed)
        total = len(rows)
        time_adherence = 1.0 if planned == 0 else min(1.5, actual/planned)
        completion_rate = 1.0 if total == 0 else completed/total
        suggested = current_daily_minutes
        warning = None
        if total >= 3 and (time_adherence < .55 or completion_rate < .5):
            suggested = max(15, round(current_daily_minutes * .8))
            warning = "planning récent trop ambitieux : charge quotidienne réduite"
        elif total >= 5 and time_adherence >= .9 and completion_rate >= .85:
            suggested = min(180, current_daily_minutes + 5)
        return AdherenceMetrics(planned,actual,completed,total,time_adherence,completion_rate,suggested,warning)
