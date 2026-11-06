from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.planning.domain.model import (
    AcademicEvent, AcademicEventKind, CoursePlanningState, EmergencyPlanner, PriorityEngine,
    ScheduleConflictDetector, StudyTaskCandidate, StudyTaskKind, TimetableEntry, TimeBoxPlanner,
)

router = APIRouter()


class StatePayload(BaseModel):
    course_id: str
    readiness: int = Field(ge=0, le=100)
    open_errors: int = Field(default=0, ge=0)
    due_flashcards: int = Field(default=0, ge=0)
    unread_sections: int = Field(default=0, ge=0)
    last_studied_at: datetime | None = None


class EventPayload(BaseModel):
    id: str
    course_id: str | None = None
    title: str
    kind: Literal['course','interrogation','exam','assignment','practical','personal']
    starts_at: datetime
    estimated_minutes: int = Field(default=60, ge=1)


class TaskPayload(BaseModel):
    id: str
    course_id: str
    title: str
    kind: Literal['read','summary','flashcards','quiz','errors','mock_exam','diagnostic']
    estimated_minutes: int = Field(ge=1)
    learning_value: float = Field(default=.5, ge=0, le=1)
    splittable: bool = True


class PlanRequest(BaseModel):
    now: datetime
    budget_minutes: int = Field(ge=5, le=600)
    states: list[StatePayload]
    events: list[EventPayload] = []
    tasks: list[TaskPayload]
    tomorrow_course_ids: list[str] = []


class TimetablePayload(BaseModel):
    id: str
    course_id: str
    weekday: int = Field(ge=1, le=7)
    start_minute: int = Field(ge=0, le=1440)
    end_minute: int = Field(ge=0, le=1440)


@router.get('/capabilities')
def capabilities() -> dict:
    return {
        'engine': 'edunova-planning',
        'version': '2',
        'features': [
            'timetable_conflicts','explainable_priority','timebox_5_15_30_60',
            'emergency_mode','local_notification_intents','assessment_replanning',
            'adaptive_availability','energy_aware_blocks','prerequisites','fatigue_guards',
            'multi_day_horizon','feasibility_analysis','plan_stability','smart_notifications',
        ],
    }


def _event(row: EventPayload) -> AcademicEvent:
    return AcademicEvent(row.id,row.course_id,row.title,AcademicEventKind(row.kind),row.starts_at,row.estimated_minutes)


def _state(row: StatePayload) -> CoursePlanningState:
    return CoursePlanningState(row.course_id,row.readiness,row.open_errors,row.due_flashcards,row.unread_sections,row.last_studied_at)


def _task(row: TaskPayload) -> StudyTaskCandidate:
    return StudyTaskCandidate(row.id,row.course_id,row.title,StudyTaskKind(row.kind),row.estimated_minutes,row.learning_value,row.splittable)


@router.post('/today')
def today(payload: PlanRequest) -> dict:
    states = {row.course_id:_state(row) for row in payload.states}
    ranked = PriorityEngine().rank(
        now=payload.now, states=states, events=[_event(row) for row in payload.events],
        tasks=[_task(row) for row in payload.tasks], tomorrow_course_ids=set(payload.tomorrow_course_ids),
    )
    plan = TimeBoxPlanner().build(now=payload.now, ranked=ranked, budget_minutes=payload.budget_minutes)
    return {
        'budget_minutes': plan.budget_minutes,
        'planned_minutes': plan.planned_minutes,
        'tasks': [
            {'id':row.id,'course_id':row.course_id,'title':row.title,'kind':row.kind.value,'minutes':row.minutes,'priority':row.priority,'reasons':list(row.reasons)}
            for row in plan.tasks
        ],
    }


@router.post('/emergency')
def emergency(payload: PlanRequest) -> dict:
    if not payload.events:
        return {'tasks': [], 'planned_minutes': 0, 'budget_minutes': payload.budget_minutes}
    event = min((_event(row) for row in payload.events), key=lambda row: row.starts_at)
    state = next((_state(row) for row in payload.states if row.course_id == event.course_id), CoursePlanningState(event.course_id or 'unknown',0))
    plan = EmergencyPlanner().build(now=payload.now,event=event,state=state,budget_minutes=payload.budget_minutes)
    return {'budget_minutes':plan.budget_minutes,'planned_minutes':plan.planned_minutes,'tasks':[{'id':t.id,'title':t.title,'kind':t.kind.value,'minutes':t.minutes} for t in plan.tasks]}


@router.post('/timetable/conflicts')
def timetable_conflicts(payload: list[TimetablePayload]) -> dict:
    rows = [TimetableEntry(row.id,row.course_id,row.weekday,row.start_minute,row.end_minute) for row in payload]
    return {'conflicts':[list(pair) for pair in ScheduleConflictDetector().find(rows)]}

# ----- Premium adaptive planning v2 -----
from app.modules.planning.domain.advanced import (
    AdaptiveCourseState, AdaptiveDayPlanner, AdaptiveTaskCandidate, AssessmentImportance,
    AvailabilityWindow, EnergyLevel, FeasibilityAnalyzer, HorizonPlanner, PlanningConstraints,
)


class AdvancedStatePayload(BaseModel):
    course_id: str
    readiness: int = Field(ge=0, le=100)
    readiness_confidence: float = Field(default=.5, ge=0, le=1)
    open_errors: int = Field(default=0, ge=0)
    due_flashcards: int = Field(default=0, ge=0)
    unread_sections: int = Field(default=0, ge=0)
    overdue_minutes: int = Field(default=0, ge=0)
    recent_study_minutes: int = Field(default=0, ge=0)
    last_studied_at: datetime | None = None


class AvailabilityPayload(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    energy: Literal['low','medium','high'] = 'medium'


class AdvancedTaskPayload(BaseModel):
    id: str
    course_id: str
    title: str
    kind: Literal['read','summary','flashcards','quiz','errors','mock_exam','diagnostic']
    remaining_minutes: int = Field(ge=1, le=5000)
    learning_value: float = Field(default=.5, ge=0, le=1)
    cognitive_load: int = Field(default=3, ge=1, le=5)
    min_chunk_minutes: int = Field(default=5, ge=5, le=120)
    max_chunk_minutes: int = Field(default=30, ge=5, le=180)
    deadline: datetime | None = None
    importance: Literal['low','normal','high','critical'] = 'normal'
    prerequisite_task_ids: list[str] = []
    assessment_id: str | None = None
    section_id: str | None = None
    pinned: bool = False
    deferred_count: int = Field(default=0, ge=0, le=100)


class ConstraintsPayload(BaseModel):
    min_block_minutes: int = Field(default=5, ge=5, le=60)
    max_block_minutes: int = Field(default=45, ge=5, le=180)
    max_continuous_minutes: int = Field(default=50, ge=5, le=240)
    break_minutes: int = Field(default=10, ge=0, le=60)
    max_courses_per_day: int = Field(default=4, ge=1, le=20)
    max_course_switches: int = Field(default=5, ge=0, le=30)
    target_readiness: int = Field(default=80, ge=0, le=100)


class AdaptivePlanRequest(BaseModel):
    now: datetime
    windows: list[AvailabilityPayload]
    states: list[AdvancedStatePayload]
    tasks: list[AdvancedTaskPayload]
    constraints: ConstraintsPayload = ConstraintsPayload()
    completed_task_ids: list[str] = []


class HorizonPlanRequest(AdaptivePlanRequest):
    horizon_days: int = Field(default=14, ge=1, le=60)


class FeasibilityRequest(BaseModel):
    now: datetime
    deadline: datetime
    required_minutes: int = Field(ge=0, le=100000)
    windows: list[AvailabilityPayload]


def _advanced_state(row: AdvancedStatePayload) -> AdaptiveCourseState:
    return AdaptiveCourseState(
        row.course_id,row.readiness,row.readiness_confidence,row.open_errors,row.due_flashcards,
        row.unread_sections,row.overdue_minutes,row.recent_study_minutes,row.last_studied_at,
    )


def _availability(row: AvailabilityPayload) -> AvailabilityWindow:
    return AvailabilityWindow(row.id,row.starts_at,row.ends_at,EnergyLevel(row.energy))


def _adaptive_task(row: AdvancedTaskPayload) -> AdaptiveTaskCandidate:
    return AdaptiveTaskCandidate(
        id=row.id,course_id=row.course_id,title=row.title,kind=StudyTaskKind(row.kind),remaining_minutes=row.remaining_minutes,
        learning_value=row.learning_value,cognitive_load=row.cognitive_load,min_chunk_minutes=row.min_chunk_minutes,
        max_chunk_minutes=row.max_chunk_minutes,deadline=row.deadline,importance=AssessmentImportance(row.importance),
        prerequisite_task_ids=tuple(row.prerequisite_task_ids),assessment_id=row.assessment_id,section_id=row.section_id,
        pinned=row.pinned,deferred_count=row.deferred_count,
    )


def _constraints(row: ConstraintsPayload) -> PlanningConstraints:
    return PlanningConstraints(
        min_block_minutes=row.min_block_minutes,max_block_minutes=row.max_block_minutes,
        max_continuous_minutes=row.max_continuous_minutes,break_minutes=row.break_minutes,
        max_courses_per_day=row.max_courses_per_day,max_course_switches=row.max_course_switches,
        target_readiness=row.target_readiness,
    )


def _block_json(row) -> dict:
    return {
        'id':row.id,'task_id':row.task_id,'course_id':row.course_id,'title':row.title,'kind':row.kind.value,
        'starts_at':row.starts_at.isoformat(),'ends_at':row.ends_at.isoformat(),'minutes':row.minutes,
        'priority':row.priority,'reasons':list(row.reasons),'window_id':row.window_id,'pinned':row.pinned,
    }


@router.post('/adaptive/day')
def adaptive_day(payload: AdaptivePlanRequest) -> dict:
    plan = AdaptiveDayPlanner().build(
        now=payload.now,windows=[_availability(w) for w in payload.windows],
        states={s.course_id:_advanced_state(s) for s in payload.states},tasks=[_adaptive_task(t) for t in payload.tasks],
        constraints=_constraints(payload.constraints),completed_task_ids=set(payload.completed_task_ids),
    )
    return {
        'date':plan.date.isoformat(),'available_minutes':plan.available_minutes,'study_minutes':plan.study_minutes,
        'break_minutes':plan.break_minutes,'utilization':plan.utilization,'warnings':list(plan.warnings),
        'blocks':[_block_json(b) for b in plan.blocks],
    }


@router.post('/adaptive/horizon')
def adaptive_horizon(payload: HorizonPlanRequest) -> dict:
    plan = HorizonPlanner().build(
        now=payload.now,windows=[_availability(w) for w in payload.windows],
        states={s.course_id:_advanced_state(s) for s in payload.states},tasks=[_adaptive_task(t) for t in payload.tasks],
        constraints=_constraints(payload.constraints),horizon_days=payload.horizon_days,completed_task_ids=set(payload.completed_task_ids),
    )
    return {
        'unscheduled_minutes':plan.unscheduled_minutes,'warnings':list(plan.warnings),'days':[
            {'date':d.date.isoformat(),'available_minutes':d.available_minutes,'study_minutes':d.study_minutes,'break_minutes':d.break_minutes,'warnings':list(d.warnings),'blocks':[_block_json(b) for b in d.blocks]}
            for d in plan.days
        ],
    }


@router.post('/adaptive/feasibility')
def adaptive_feasibility(payload: FeasibilityRequest) -> dict:
    report = FeasibilityAnalyzer().analyze(
        now=payload.now,deadline=payload.deadline,required_minutes=payload.required_minutes,
        windows=[_availability(w) for w in payload.windows],
    )
    return {
        'feasible':report.feasible,'required_minutes':report.required_minutes,'available_minutes':report.available_minutes,
        'deficit_minutes':report.deficit_minutes,'warnings':list(report.warnings),
    }
