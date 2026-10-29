"""Phase 15 v0.50.1: evidence-backed period comparison and disclosure guards.

Uses the real SQLAlchemy repository (in-memory SQLite), not mocked analytics.
This does not constitute PostgreSQL certification or formal differential privacy.
"""
from datetime import timedelta
from uuid import uuid4
import pytest

from app.modules.campus.domain.model import CampusRole, PeriodKind, UnitKind
from app.modules.teaching.domain.model import TeacherRole
from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
from app.modules.institutional_analytics.api.router import router
from test_institutional_analytics_lot27 import seed, NOW
from test_phase15_institutional_intelligence import _add_students


def periods():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    year=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,
                       name='2027-2028', starts_on=NOW.date()+timedelta(days=401),
                       ends_on=NOW.date()+timedelta(days=700), parent_id=None)
    after=cs.add_period('owner',i.id,kind=PeriodKind.SEMESTER,
                        name='S1 2027',starts_on=NOW.date()+timedelta(days=401),
                        ends_on=NOW.date()+timedelta(days=491), parent_id=year.id)
    future=cs.create_cohort('owner',i.id,program_unit_id=cohort.program_unit_id,
                            academic_period_id=after.id,name='BAC2',level='2')
    ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=future.id,
                       academic_period_id=after.id,label='BIO 2027')
    return cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future


def five_disjoint():
    fixture=periods()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=fixture
    _add_students(cs,i.id,cohort.id,'old2','old3','old4','old5')
    _add_students(cs,i.id,future.id,'new1','new2','new3','new4','new5')
    return fixture


def compare(f,actor='owner',unit=None):
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    return ia.compare_period_briefs(actor,i.id,previous_period_id=p.id,
                                    current_period_id=after.id,academic_unit_id=unit)


def test_period_comparison_requires_two_disjoint_groups_with_five_students():
    fixture=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=fixture
    future_off_id=ia.repo.offering_ids(i.id,after.id,future.id)[0]
    ts.assign_teacher('owner',i.id,future_off_id,teacher_account_id='teacher',role=TeacherRole.LEAD)
    new_off=ts.repo.offering(i.id,future_off_id)
    ts.publish_offering('owner',i.id,future_off_id,new_off.row_version)
    for offering_id in (off.id,future_off_id):
        for n in range(3):
            sess=ts.add_session('owner',i.id,offering_id,title=f'Course {n}',
                                starts_at=NOW+timedelta(hours=3*n),
                                ends_at=NOW+timedelta(hours=3*n+1))
            if (n==0 if offering_id==off.id else n>0):
                ts.complete_session('owner',i.id,sess.id,summary='completed',expected_version=sess.row_version)
    result=compare(fixture)
    teaching=result['metrics']['teaching.completion_rate']
    assert result['comparison_policy']['data_release']=='eligible'
    assert teaching['previous']==33.33 and teaching['current']==66.67
    assert teaching['delta_percentage_points']==33.34
    assert teaching['status']=='comparable'
    assert result['metrics']['results.pass_rate']['status']=='source_unavailable_or_version_mismatch'
    assert result['metrics']['results.pass_rate']['delta_percentage_points'] is None
    assert all('denominator' not in metric for metric in result['metrics'].values())
    assert result['comparison_policy']['automatic_decision'] is False


def test_comparison_suppresses_when_a_period_has_only_four_people():
    f=periods()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    _add_students(cs,i.id,cohort.id,'old2','old3','old4')
    _add_students(cs,i.id,future.id,'new1','new2','new3','new4','new5')
    result=compare(f)
    assert result['comparison_policy']['data_release']=='privacy_suppressed'
    for metric in result['metrics'].values():
        assert metric['status']=='privacy_suppressed'
        assert metric['previous'] is None and metric['current'] is None
        assert metric['delta_percentage_points'] is None
    assert 'unique_active_students' not in str(result)


def test_comparison_suppresses_overlapping_students_without_exposing_overlap_count():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    cs.enroll('owner',i.id,cohort_id=future.id,student_account_id='old2')
    result=compare(f)
    assert result['comparison_policy']['data_release']=='privacy_suppressed'
    assert all(x['delta_percentage_points'] is None for x in result['metrics'].values())
    assert 'overlap' not in result['comparison_policy']  # don't leak membership count
    assert 'old2' not in str(result)


def test_period_comparison_requires_valid_kind_order_and_tenant_periods():
    f=periods()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    with pytest.raises(ValueError,match='distinct_periods'):
        ia.compare_period_briefs('owner',i.id,previous_period_id=p.id,current_period_id=p.id)
    with pytest.raises(ValueError,match='incomparable_periods'):
        ia.compare_period_briefs('owner',i.id,previous_period_id=after.id,current_period_id=p.id)
    with pytest.raises(ValueError,match='period_not_found'):
        ia.compare_period_briefs('owner',i.id,previous_period_id=p.id,current_period_id='foreign')
    y=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,
                    name='2060',starts_on=NOW.date()+timedelta(days=900),
                    ends_on=NOW.date()+timedelta(days=1200),parent_id=None)
    with pytest.raises(ValueError,match='incomparable_periods'):
        ia.compare_period_briefs('owner',i.id,previous_period_id=p.id,current_period_id=y.id)


def test_comparison_rejects_student_teacher_faculty_outside_unit_and_foreign_tenant():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    for actor in ('teacher','student','outsider'):
        with pytest.raises(PermissionError):compare(f,actor)
    fa=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='F1',code='F1',parent_id=None)
    fb=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='F2',code='F2',parent_id=None)
    cs.invite_member('owner',i.id,account_id='faculty',role=CampusRole.FACULTY_ADMIN,unit_id=fa.id)
    cs.accept_invitation('faculty',i.id)
    with pytest.raises(PermissionError):compare(f,'faculty')
    with pytest.raises(PermissionError):compare(f,'faculty',fb.id)
    assert compare(f,'faculty',fa.id)['comparison_policy']['data_release']=='privacy_suppressed'  # no members under F1
    other=cs.create_institution('other_owner',name='Other',slug='other-uni-15',
            legal_name='',country_code='CD',city='Goma',logo_url=None)
    with pytest.raises(PermissionError):
        ia.compare_period_briefs('other_owner',i.id,previous_period_id=p.id,current_period_id=after.id)
    with pytest.raises(ValueError,match='period_not_found'):
        ia.compare_period_briefs('owner',i.id,previous_period_id=p.id,current_period_id='some-other-tenant-period')


def test_foreign_enrollment_does_not_increase_submission_opportunities():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    a=ass.create('owner',i.id,off.id,title='Submit',due_at=NOW+timedelta(days=5))
    ass.publish('owner',i.id,a.id,a.row_version)
    baseline=ia.repo.snapshot(i.id,p.id,offering_id=off.id,governed=True)
    assert baseline['assignments']['submission_opportunities']==5
    # Corrupted cross-tenant row must not count as a student of this university.
    with ia.repo.sf() as db:
        db.add(EnrollmentRow(id=uuid4().hex,institution_id='foreign',cohort_id=cohort.id,
                             student_account_id='outsider',active=True,created_at=NOW))
        db.commit()
    updated=ia.repo.snapshot(i.id,p.id,offering_id=off.id,governed=True)
    assert updated['assignments']['submission_opportunities']==5


def test_assignment_single_submitter_is_not_disclosed_even_with_many_assignments():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    for j in range(3):
        a=ass.create('owner',i.id,off.id,title=f'Assignment {j}',due_at=NOW+timedelta(days=5))
        ass.publish('owner',i.id,a.id,a.row_version)
        ass.submit('student',i.id,a.id,text_content='work')
    report=ia.decision_brief('owner',i.id,offering_id=off.id)
    metric=report['metrics']['assignments.submission_rate']
    assert metric['status']=='suppressed_small_population'
    assert metric['value'] is None and metric['denominator'] is None
    assert report['data_quality']['unique_active_students']==5


def test_period_comparison_is_authenticated_endpoint():
    r=[r for r in router.routes if r.path.endswith('/intelligence/period-comparison')]
    assert len(r)==1
    assert r[0].methods=={'GET'}
    assert any(d.call.__name__=='current_auth' for d in r[0].dependant.dependencies)


def test_inactive_cohort_cannot_increase_comparison_population():
    fixture=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=fixture
    # Simulate archived cohort still referenced by a persisted offering.
    from app.modules.campus.infrastructure.sqlalchemy_repo import CohortRow
    with ia.repo.sf() as db:
        db.get(CohortRow,cohort.id).active=False
        db.commit()
    result=compare(fixture)
    assert ia.repo.distinct_active_students(i.id,p.id)==0
    assert result['comparison_policy']['data_release']=='privacy_suppressed'
    assert all(m['delta_percentage_points'] is None for m in result['metrics'].values())


def test_metrics_fail_closed_without_student_contributor_provenance():
    from app.modules.institutional_analytics.application.service import InstitutionalAnalyticsService
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    src=ia.repo.snapshot(i.id,p.id,offering_id=off.id,governed=True)
    src['_metric_contributors']={}  # corrupt/missing source provenance
    output=InstitutionalAnalyticsService._governed_metrics(src,5)
    for metric in InstitutionalAnalyticsService.STUDENT_METRICS:
        assert output[metric]['value'] is None
        assert output[metric]['status']=='suppressed_small_population' or output[metric]['status']=='unavailable'
    assert set(m['source_contract'] for m in output.values())=={
        'institutional_teaching_sessions','closed_clear_attendance',
        'eligible_assignment_submissions','published_validated_gradebook'}


def test_cross_tenant_duplicate_identity_does_not_fake_period_overlap():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    with ia.repo.sf() as db:
        db.add(EnrollmentRow(id=uuid4().hex,institution_id='foreign-uni',cohort_id=future.id,
            student_account_id='old2',active=True,created_at=NOW))
        db.commit()
    assert ia.repo.period_population_overlap(i.id,p.id,after.id)==0
    assert compare(f)['comparison_policy']['data_release']=='eligible'
