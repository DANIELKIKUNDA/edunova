from datetime import datetime, timedelta, timezone

import pytest

from app.modules.planning.domain.advanced import (
    AdaptiveCourseState, AdaptiveDayPlanner, AdaptivePriorityEngine, AdaptiveTaskCandidate,
    AssessmentImportance, AvailabilityWindow, EnergyLevel, FeasibilityAnalyzer, HorizonPlanner,
    PlanReconciler, PlanningConstraints, SmartNotificationPlanner,
)
from app.modules.planning.domain.model import NotificationIntent, StudyTaskKind
from app.shared.domain.errors import ValidationError

NOW = datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc)


def task(id: str, course: str, minutes: int = 30, **kw):
    return AdaptiveTaskCandidate(id=id, course_id=course, title=id, kind=kw.pop('kind', StudyTaskKind.READ), remaining_minutes=minutes, **kw)


def window(id: str, start_h: int, end_h: int, *, day: int = 0, energy=EnergyLevel.MEDIUM):
    base = NOW + timedelta(days=day)
    return AvailabilityWindow(id, base.replace(hour=start_h), base.replace(hour=end_h), energy)


def test_priority_boosts_pinned_and_deferred_tasks():
    state = {'bio': AdaptiveCourseState('bio', 50)}
    rows = AdaptivePriorityEngine().rank(now=NOW, states=state, tasks=[task('a','bio'), task('b','bio', pinned=True), task('c','bio', deferred_count=3)])
    assert rows[0].task.id == 'b'
    assert any(r.task.id == 'c' and 'reportée 3 fois' in r.reasons for r in rows)


def test_priority_blocks_unmet_prerequisite():
    rows = AdaptivePriorityEngine().rank(now=NOW, states={'c':AdaptiveCourseState('c',40)}, tasks=[task('advanced','c', prerequisite_task_ids=('intro',))], completed_task_ids=set())
    assert rows == ()
    rows = AdaptivePriorityEngine().rank(now=NOW, states={'c':AdaptiveCourseState('c',40)}, tasks=[task('advanced','c', prerequisite_task_ids=('intro',))], completed_task_ids={'intro'})
    assert len(rows) == 1


def test_high_cognitive_task_is_not_scheduled_in_low_energy_window_when_ineligible():
    planner = AdaptiveDayPlanner()
    plan = planner.build(now=NOW, windows=[window('w',8,9,energy=EnergyLevel.LOW)], states={'c':AdaptiveCourseState('c',20)}, tasks=[task('hard','c', cognitive_load=5)])
    assert plan.blocks == ()


def test_low_energy_window_prefers_light_task_over_heavy():
    planner = AdaptiveDayPlanner()
    tasks = [task('hard','c', cognitive_load=5, learning_value=1), task('light','c', cognitive_load=1, learning_value=.6)]
    plan = planner.build(now=NOW, windows=[window('w',8,9,energy=EnergyLevel.LOW)], states={'c':AdaptiveCourseState('c',20)}, tasks=tasks)
    assert plan.blocks[0].task_id == 'light'


def test_day_planner_respects_availability_and_breaks():
    constraints = PlanningConstraints(max_block_minutes=25, max_continuous_minutes=25, break_minutes=10)
    plan = AdaptiveDayPlanner().build(now=NOW, windows=[window('w',8,10)], states={'c':AdaptiveCourseState('c',20)}, tasks=[task('long','c',90,max_chunk_minutes=25)], constraints=constraints)
    assert all(NOW <= b.starts_at < b.ends_at <= NOW.replace(hour=10) for b in plan.blocks)
    assert plan.break_minutes >= 20
    assert plan.study_minutes <= plan.available_minutes


def test_day_planner_caps_course_diversity():
    tasks = [task(f't{i}',f'c{i}',15, learning_value=1) for i in range(5)]
    states = {f'c{i}':AdaptiveCourseState(f'c{i}',20) for i in range(5)}
    plan = AdaptiveDayPlanner().build(now=NOW, windows=[window('w',8,12)], states=states, tasks=tasks, constraints=PlanningConstraints(max_courses_per_day=2))
    assert len({b.course_id for b in plan.blocks}) <= 2


def test_day_planner_does_not_overbook_window():
    plan = AdaptiveDayPlanner().build(now=NOW, windows=[window('w',8,9)], states={'c':AdaptiveCourseState('c',20)}, tasks=[task('long','c',200)])
    assert plan.study_minutes + plan.break_minutes <= plan.available_minutes


def test_feasibility_report_detects_deficit():
    report = FeasibilityAnalyzer().analyze(now=NOW, deadline=NOW+timedelta(hours=2), required_minutes=150, windows=[window('w',8,10)])
    assert not report.feasible
    assert report.deficit_minutes == 30
    assert report.warnings


def test_horizon_carries_remaining_work_across_days():
    windows = [window('d1',8,9,day=0), window('d2',8,9,day=1)]
    plan = HorizonPlanner().build(now=NOW, windows=windows, states={'c':AdaptiveCourseState('c',20)}, tasks=[task('long','c',90,max_chunk_minutes=30)], horizon_days=2)
    assert len(plan.days) == 2
    assert sum(d.study_minutes for d in plan.days) > 0
    assert plan.unscheduled_minutes < 90


def test_horizon_warns_when_deadlined_work_remains_unscheduled():
    windows = [window('d1',8,9,day=0)]
    t = task('long','c',180,deadline=NOW+timedelta(hours=5))
    plan = HorizonPlanner().build(now=NOW, windows=windows, states={'c':AdaptiveCourseState('c',20)}, tasks=[t], horizon_days=1)
    assert any('échéance' in w for w in plan.warnings)


def test_reconciler_preserves_completed_and_pinned_blocks():
    planner = AdaptiveDayPlanner()
    old = planner.build(now=NOW, windows=[window('w',8,9)], states={'c':AdaptiveCourseState('c',20)}, tasks=[task('a','c',20,pinned=True)])
    fresh = planner.build(now=NOW, windows=[window('w',8,9)], states={'d':AdaptiveCourseState('d',20)}, tasks=[task('b','d',20)])
    reconciled = PlanReconciler().reconcile(old_blocks=old.blocks, fresh=fresh, completed_block_ids=set(), pinned_block_ids={old.blocks[0].id})
    assert any(b.task_id == 'a' for b in reconciled.blocks)


def test_smart_notifications_shift_out_of_quiet_hours_and_cap_day():
    event_at = NOW.replace(hour=12)
    intents = [
        NotificationIntent('e', NOW.replace(hour=23), 'E','B','j-3'),
        NotificationIntent('e', NOW.replace(hour=9), 'E','B','j-1'),
        NotificationIntent('e2', NOW.replace(hour=10), 'E2','B','change'),
    ]
    rows = SmartNotificationPlanner().optimize(intents=intents, event_starts={'e':event_at,'e2':event_at}, quiet_start_minute=22*60, quiet_end_minute=7*60, max_per_day=2)
    assert len([r for r in rows if r.fire_at.date() == NOW.date()]) <= 2
    assert all(not (r.fire_at.hour >= 22 or r.fire_at.hour < 7) for r in rows)


def test_invalid_constraints_are_rejected():
    with pytest.raises(ValidationError):
        PlanningConstraints(min_block_minutes=2)


def test_deadline_importance_increases_priority():
    deadline = NOW+timedelta(days=2)
    rows = AdaptivePriorityEngine().rank(
        now=NOW, states={'a':AdaptiveCourseState('a',50),'b':AdaptiveCourseState('b',50)},
        tasks=[task('normal','a',deadline=deadline,importance=AssessmentImportance.NORMAL), task('critical','b',deadline=deadline,importance=AssessmentImportance.CRITICAL)],
    )
    assert rows[0].task.id == 'critical'


def test_low_readiness_confidence_prioritizes_diagnostic_evidence():
    state = {'c':AdaptiveCourseState('c',readiness=70,readiness_confidence=.2)}
    rows = AdaptivePriorityEngine().rank(now=NOW, states=state, tasks=[task('diag','c',kind=StudyTaskKind.DIAGNOSTIC), task('read','c',kind=StudyTaskKind.READ)])
    assert rows[0].task.id == 'diag'


def test_window_requires_timezone_awareness():
    naive = datetime(2026,9,20,8,0)
    with pytest.raises(ValidationError):
        AvailabilityWindow('w',naive,naive+timedelta(hours=1))


def test_assessment_factory_builds_explainable_workload_and_tasks():
    from app.modules.planning.domain.advanced import AssessmentPreparationFactory, AssessmentScope
    scope=AssessmentScope('exam','bio',NOW+timedelta(days=7),section_ids=('s1','s2'),target_readiness=85,importance=AssessmentImportance.HIGH)
    state=AdaptiveCourseState('bio',readiness=45,readiness_confidence=.3,open_errors=5,due_flashcards=12,unread_sections=3)
    prep=AssessmentPreparationFactory().build(state=state,scope=scope)
    assert prep.estimated_minutes>0
    kinds={t.kind for t in prep.tasks}
    assert StudyTaskKind.READ in kinds
    assert StudyTaskKind.DIAGNOSTIC in kinds
    assert StudyTaskKind.QUIZ in kinds
    assert StudyTaskKind.MOCK_EXAM in kinds
    assert any('section' in r for r in prep.reasons)


def test_assessment_factory_honors_manual_required_minutes_override():
    from app.modules.planning.domain.advanced import AssessmentPreparationFactory, AssessmentScope
    scope=AssessmentScope('exam','bio',NOW+timedelta(days=2),required_minutes_override=90)
    prep=AssessmentPreparationFactory().build(state=AdaptiveCourseState('bio',50),scope=scope)
    assert prep.estimated_minutes==90


def test_assessment_factory_rejects_course_mismatch():
    from app.modules.planning.domain.advanced import AssessmentPreparationFactory, AssessmentScope
    with pytest.raises(ValidationError):
        AssessmentPreparationFactory().build(state=AdaptiveCourseState('math',50),scope=AssessmentScope('e','bio',NOW+timedelta(days=1)))


def test_availability_deriver_subtracts_classes_from_preferred_study_time():
    from app.modules.planning.domain.advanced import AvailabilityDeriver, BusyInterval
    preferred=[AvailabilityWindow('p',NOW,NOW+timedelta(hours=4),EnergyLevel.HIGH)]
    busy=[BusyInterval('class',NOW+timedelta(hours=1),NOW+timedelta(hours=2))]
    free=AvailabilityDeriver().derive(preferred=preferred,busy=busy)
    assert [(w.starts_at,w.ends_at) for w in free]==[(NOW,NOW+timedelta(hours=1)),(NOW+timedelta(hours=2),NOW+timedelta(hours=4))]


def test_availability_deriver_drops_tiny_fragments():
    from app.modules.planning.domain.advanced import AvailabilityDeriver, BusyInterval
    preferred=[AvailabilityWindow('p',NOW,NOW+timedelta(minutes=30))]
    busy=[BusyInterval('class',NOW+timedelta(minutes=5),NOW+timedelta(minutes=30))]
    assert AvailabilityDeriver().derive(preferred=preferred,busy=busy,min_window_minutes=10)==()


def test_adherence_analyzer_reduces_unrealistic_daily_budget():
    from app.modules.planning.domain.advanced import AdherenceAnalyzer, StudySessionRecord
    rows=[StudySessionRecord(60,20,False,NOW-timedelta(days=i)) for i in range(4)]
    metrics=AdherenceAnalyzer().analyze(sessions=rows,current_daily_minutes=60)
    assert metrics.suggested_daily_minutes==48
    assert metrics.warning is not None


def test_adherence_analyzer_only_increases_after_consistent_execution():
    from app.modules.planning.domain.advanced import AdherenceAnalyzer, StudySessionRecord
    rows=[StudySessionRecord(30,30,True,NOW-timedelta(days=i)) for i in range(6)]
    metrics=AdherenceAnalyzer().analyze(sessions=rows,current_daily_minutes=30)
    assert metrics.suggested_daily_minutes==35
    assert metrics.completion_rate==1


def test_assessment_override_scales_task_minutes_to_exact_total():
    from app.modules.planning.domain.advanced import AssessmentPreparationFactory, AssessmentScope
    scope=AssessmentScope('exam','bio',NOW+timedelta(days=2),required_minutes_override=120)
    state=AdaptiveCourseState('bio',40,readiness_confidence=.2,open_errors=2,due_flashcards=5,unread_sections=2)
    prep=AssessmentPreparationFactory().build(state=state,scope=scope)
    assert sum(t.remaining_minutes for t in prep.tasks)==120


def test_assessment_override_rejects_impossibly_small_total():
    from app.modules.planning.domain.advanced import AssessmentPreparationFactory, AssessmentScope
    scope=AssessmentScope('exam','bio',NOW+timedelta(days=2),required_minutes_override=5)
    state=AdaptiveCourseState('bio',40,readiness_confidence=.2,open_errors=2,due_flashcards=5,unread_sections=2)
    with pytest.raises(ValidationError):
        AssessmentPreparationFactory().build(state=state,scope=scope)
