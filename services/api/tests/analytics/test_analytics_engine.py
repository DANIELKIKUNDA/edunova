from datetime import UTC, datetime

import pytest

from app.modules.analytics.domain.engine import AnalyticsEngine
from app.modules.analytics.domain.model import AnalyticsSnapshot, CourseAnalyticsSignal, RecommendationKind, TrendDirection
from app.shared.domain.errors import ValidationError


def snapshot(**overrides):
    base=dict(
        generated_at=datetime(2026,9,22,8,tzinfo=UTC),
        study_minutes_7d=240, study_minutes_prev_7d=160,
        quiz_accuracy_7d=.78, quiz_accuracy_prev_7d=.61,
        plan_adherence_7d=.72, active_days_7d=5, streak_days=4,
        courses=(),
    )
    base.update(overrides)
    return AnalyticsSnapshot(**base)


def test_momentum_improves_when_study_and_quiz_improve():
    report=AnalyticsEngine().build(snapshot())
    assert report.momentum==TrendDirection.IMPROVING
    assert report.study_time.delta==80
    assert report.quiz_accuracy and report.quiz_accuracy.direction==TrendDirection.IMPROVING


def test_near_term_low_readiness_is_high_risk_and_first_recommendation():
    c=CourseAnalyticsSignal(course_id='bio',title='Biochimie',coverage=.5,quiz_mastery=.45,flashcard_mastery=.6,weakness_recovery=.4,open_errors=9,overdue_flashcards=12,days_to_next_assessment=2,next_assessment_readiness=44)
    report=AnalyticsEngine().build(snapshot(courses=(c,)))
    assert report.course_insights[0].risk_level=='high'
    assert report.recommendations[0].kind==RecommendationKind.ASSESSMENT_FOCUS
    assert report.recommendations[0].priority_score>=80


def test_recommendations_are_diversified_and_capped_at_five():
    courses=tuple(CourseAnalyticsSignal(course_id=f'c{i}',title=f'Cours {i}',coverage=.2,quiz_mastery=.3,open_errors=15,overdue_flashcards=20,days_to_next_assessment=3,next_assessment_readiness=30) for i in range(4))
    report=AnalyticsEngine().build(snapshot(courses=courses))
    assert len(report.recommendations)==5
    counts={}
    for item in report.recommendations:
        counts[item.course_id]=counts.get(item.course_id,0)+1
    assert max(counts.values())<=2


def test_low_plan_adherence_recommends_recovery_without_shaming_language():
    report=AnalyticsEngine().build(snapshot(plan_adherence_7d=.35))
    rec=next(x for x in report.recommendations if x.kind==RecommendationKind.PLAN_RECOVERY)
    assert 'réaliste' in rec.reason.lower()
    assert 'échec' not in rec.reason.lower()


def test_missing_signals_do_not_produce_fake_readiness():
    c=CourseAnalyticsSignal(course_id='law',title='Droit',open_errors=0)
    report=AnalyticsEngine().build(snapshot(courses=(c,)))
    assert report.course_insights[0].readiness is None


def test_partial_readiness_renormalizes_available_weights():
    c=CourseAnalyticsSignal(course_id='math',title='Mathématiques',coverage=1.0,quiz_mastery=.5)
    report=AnalyticsEngine().build(snapshot(courses=(c,)))
    # (1*.30 + .5*.40) / .70 = .714...
    assert report.course_insights[0].readiness==71


def test_snapshot_rejects_invalid_ratios_and_negative_counters():
    with pytest.raises(ValidationError):
        snapshot(active_days_7d=8)
    with pytest.raises(ValidationError):
        CourseAnalyticsSignal(course_id='x',title='X',quiz_mastery=1.2)


def test_report_explicitly_disclaims_grade_prediction():
    report=AnalyticsEngine().build(snapshot())
    assert 'ne prédisent pas ta note' in report.explanation.lower()


def test_limited_evidence_avoids_overconfident_momentum():
    report=AnalyticsEngine().build(snapshot(active_days_7d=1,study_minutes_7d=200,study_minutes_prev_7d=0))
    assert report.evidence.value=="limited"
    assert report.momentum==TrendDirection.STABLE
