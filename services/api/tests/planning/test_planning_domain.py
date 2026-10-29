from datetime import datetime, timedelta, timezone

import pytest

from app.modules.planning.domain.model import (
    AcademicEvent, AcademicEventKind, CoursePlanningState, EmergencyPlanner, NotificationPlanner,
    PriorityEngine, ScheduleConflictDetector, StudyTaskCandidate, StudyTaskKind, TimetableEntry, TimeBoxPlanner,
)
from app.shared.domain.errors import ValidationError

NOW = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)


def test_schedule_conflict_detector_catches_overlap_only_same_day():
    rows = [
        TimetableEntry('a','c1',1,480,540), TimetableEntry('b','c2',1,530,600), TimetableEntry('c','c3',2,530,600),
    ]
    assert ScheduleConflictDetector().find(rows) == (('a','b'),)


def test_priority_favors_imminent_low_readiness_course():
    events = [AcademicEvent('e','bio','Bio exam',AcademicEventKind.EXAM,NOW+timedelta(days=2))]
    states = {'bio': CoursePlanningState('bio', readiness=30, open_errors=6), 'math': CoursePlanningState('math', readiness=80)}
    tasks = [
        StudyTaskCandidate('bio-q','bio','Quiz Bio',StudyTaskKind.QUIZ,15,.8),
        StudyTaskCandidate('math-q','math','Quiz Math',StudyTaskKind.QUIZ,15,.8),
    ]
    ranked = PriorityEngine().rank(now=NOW, states=states, events=events, tasks=tasks)
    assert ranked[0].task.course_id == 'bio'
    assert 'évaluation dans ≤3 jours' in ranked[0].reasons


def test_tomorrow_course_gets_small_priority_boost():
    states = {'c1': CoursePlanningState('c1', readiness=70), 'c2': CoursePlanningState('c2', readiness=70)}
    tasks = [StudyTaskCandidate('a','c1','A',StudyTaskKind.READ,10,.5), StudyTaskCandidate('b','c2','B',StudyTaskKind.READ,10,.5)]
    ranked = PriorityEngine().rank(now=NOW, states=states, events=[], tasks=tasks, tomorrow_course_ids={'c2'})
    assert ranked[0].task.course_id == 'c2'


def test_timebox_never_exceeds_budget_and_can_split():
    task = StudyTaskCandidate('a','c','Long',StudyTaskKind.READ,40,.9,splittable=True)
    ranked = PriorityEngine().rank(now=NOW, states={'c':CoursePlanningState('c',20)}, events=[], tasks=[task])
    plan = TimeBoxPlanner().build(now=NOW, ranked=ranked, budget_minutes=15)
    assert plan.planned_minutes == 15


def test_timebox_skips_unsplittable_task_that_does_not_fit():
    task = StudyTaskCandidate('a','c','Mock',StudyTaskKind.MOCK_EXAM,40,.9,splittable=False)
    ranked = PriorityEngine().rank(now=NOW, states={'c':CoursePlanningState('c',20)}, events=[], tasks=[task])
    plan = TimeBoxPlanner().build(now=NOW, ranked=ranked, budget_minutes=15)
    assert plan.tasks == ()


def test_emergency_plan_requires_assessment_within_36_hours():
    event = AcademicEvent('e','bio','Interro',AcademicEventKind.INTERROGATION,NOW+timedelta(hours=20))
    plan = EmergencyPlanner().build(now=NOW,event=event,state=CoursePlanningState('bio',40,open_errors=5),budget_minutes=60)
    assert plan.planned_minutes == 60
    assert plan.tasks[0].kind == StudyTaskKind.DIAGNOSTIC
    late = AcademicEvent('late','bio','Interro',AcademicEventKind.INTERROGATION,NOW+timedelta(days=3))
    with pytest.raises(ValidationError):
        EmergencyPlanner().build(now=NOW,event=late,state=CoursePlanningState('bio',40))


def test_notification_intents_are_future_only():
    event = AcademicEvent('e','bio','Interro Bio',AcademicEventKind.INTERROGATION,NOW+timedelta(days=5))
    intents = NotificationPlanner().for_event(now=NOW,event=event,readiness=35)
    assert len(intents) == 3
    assert all(intent.fire_at > NOW for intent in intents)


def test_schedule_text_parser_parses_reviewable_rows():
    from app.modules.planning.application.schedule_import import ScheduleTextParser
    rows = ScheduleTextParser().parse('Lundi 08:00-10:00 Anatomie\nMercredi 14h30–16h00 Chimie')
    assert [(r.weekday,r.start_minute,r.end_minute,r.label) for r in rows] == [
        (1,480,600,'Anatomie'),(3,870,960,'Chimie')
    ]
