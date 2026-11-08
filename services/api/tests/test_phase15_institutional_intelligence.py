"""Phase 15 foundation: real SQL/RBAC adversarial tests for governed intelligence.

No production PostgreSQL, external provider, or mobile-device claim is made here.
"""
import pytest
from datetime import timedelta

from app.modules.campus.domain.model import CampusRole, UnitKind, PeriodKind
from app.modules.teaching.domain.model import TeacherRole
from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
from app.modules.gradebook.infrastructure.sqlalchemy_repo import GradebookRow, ComponentRow, MarkRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceRecordRow, AttendanceSessionRow
from test_institutional_analytics_lot27 import seed, NOW


def _add_students(cs, iid, cohort_id, *names):
    for name in names:
        cs.invite_member('owner', iid, account_id=name, role=CampusRole.STUDENT, unit_id=None)
        cs.accept_invitation(name, iid)
        cs.enroll('owner', iid, cohort_id=cohort_id, student_account_id=name)


def test_small_cohort_suppresses_all_sensitive_rates_and_findings():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off = seed()
    brief = ia.decision_brief('owner', i.id, academic_period_id=p.id, offering_id=off.id)
    assert brief['contract_version'] == 1
    assert brief['data_quality']['status'] == 'insufficient_population'
    assert brief['data_quality']['unique_active_students'] is None
    assert brief['findings'] == []
    assert all(x['value'] is None and x['denominator'] is None for x in brief['metrics'].values())
    assert all(x['status']=='suppressed_small_population' for x in brief['metrics'].values())
    assert brief['policy']['automatic_decision'] is False
    assert 'student' not in str(brief['metrics'])


def test_three_distinct_active_students_release_only_well_supported_indicators():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off = seed()
    _add_students(cs, i.id, cohort.id, 's2', 's3')
    for idx in range(3):
        sess=ts.add_session('teacher',i.id,off.id,title=f'Cours {idx}',
            starts_at=NOW+timedelta(hours=idx*3),ends_at=NOW+timedelta(hours=idx*3+1))
        if idx==0:
            ts.complete_session('teacher',i.id,sess.id,summary='fait',expected_version=sess.row_version)
    b=ia.decision_brief('owner',i.id,academic_period_id=p.id,cohort_id=cohort.id)
    assert b['data_quality']['unique_active_students']==3
    assert b['metrics']['teaching.completion_rate']['value']==33.33
    assert b['metrics']['teaching.completion_rate']['denominator']==3
    assert b['metrics']['results.pass_rate']['value'] is None  # no published results
    assert b['metrics']['results.pass_rate']['denominator'] is None
    assert any(x['metric']=='teaching.completion_rate' for x in b['findings'])
    assert all(x['automatic_decision'] is False for x in b['findings'])


def test_teacher_student_and_nonmember_cannot_access_decision_brief():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    for actor in ('teacher','student','intruder'):
        with pytest.raises(PermissionError):
            ia.decision_brief(actor,i.id,offering_id=off.id)


def test_cross_university_membership_never_authorizes_foreign_university():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    other=cs.create_institution('otherowner',name='Université B',slug='univ-b',legal_name='',country_code='CD',city='Goma',logo_url=None)
    with pytest.raises(PermissionError):
        ia.decision_brief('otherowner',i.id,offering_id=off.id)
    with pytest.raises(ValueError, match='offering_not_found'):
        ia.decision_brief('owner',i.id,offering_id='foreign-offering')
    with pytest.raises(ValueError, match='cohort_not_found'):
        ia.decision_brief('owner',i.id,cohort_id='foreign-cohort')
    with pytest.raises(PermissionError):
        ia.decision_brief('owner',other.id)


def test_scope_combination_cannot_leak_different_cohort_or_period():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    other_period=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,
        name='S2',starts_on=NOW.date()+timedelta(days=110),
        ends_on=NOW.date()+timedelta(days=190),parent_id=None)
    with pytest.raises(ValueError,match='scope_mismatch'):
        ia.decision_brief('owner',i.id,offering_id=off.id,academic_period_id=other_period.id)
    with pytest.raises(ValueError,match='scope_mismatch'):
        ia.decision_brief('owner',i.id,cohort_id=cohort.id,academic_period_id=other_period.id)
    with pytest.raises(ValueError,match='period_not_found'):
        ia.decision_brief('owner',i.id,academic_period_id='fake-period')
    with pytest.raises(ValueError,match='ambiguous_scope'):
        ia.decision_brief('owner',i.id,academic_unit_id=cohort.program_unit_id,offering_id=off.id)


def test_faculty_admin_cannot_view_global_parent_or_sibling_unit():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    fa=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Sciences',code='SCI',parent_id=None)
    pa=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Pharmacie',code='PHA',parent_id=fa.id)
    fb=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Arts',code='ART',parent_id=None)
    cs.invite_member('owner',i.id,account_id='faculty',role=CampusRole.FACULTY_ADMIN,unit_id=fa.id)
    cs.accept_invitation('faculty',i.id)
    assert ia.decision_brief('faculty',i.id,academic_unit_id=fa.id)['scope']['academic_unit_id']==fa.id
    assert ia.decision_brief('faculty',i.id,academic_unit_id=pa.id)['scope']['academic_unit_id']==pa.id
    for unit in (None,fb.id,cohort.program_unit_id):
        with pytest.raises(PermissionError):
            ia.decision_brief('faculty',i.id,academic_unit_id=unit)


def test_unscoped_faculty_role_cannot_bypass_unit_filter():
    cs, ts, ass, gs, ops, ia, i, p, cohort, off=seed()
    unit=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Sci',code='SCIX',parent_id=None)
    cs.invite_member('owner',i.id,account_id='unscoped-faculty',role=CampusRole.FACULTY_ADMIN,unit_id=unit.id)
    cs.accept_invitation('unscoped-faculty',i.id)
    # Adversarial malformed historic membership; fail closed even if DB is corrupted.
    from app.modules.campus.infrastructure.sqlalchemy_repo import MembershipRow
    from sqlalchemy import select
    with ia.repo.sf() as s:
        row=s.scalar(select(MembershipRow).where(MembershipRow.institution_id==i.id,MembershipRow.account_id=='unscoped-faculty'))
        row.unit_id=None;s.commit()
    with pytest.raises(PermissionError,match='faculty_unit_required'):
        ia.decision_brief('unscoped-faculty',i.id)


def test_duplicate_enrollments_across_two_cohorts_do_not_bypass_k_anonymity():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    for idx in range(2):
        c=cs.create_cohort('owner',i.id,program_unit_id=cohort.program_unit_id,
            academic_period_id=p.id,name=f'B{idx}',level='1')
        cs.enroll('owner',i.id,cohort_id=c.id,student_account_id='student')
        ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=c.id,
            academic_period_id=p.id,label=f'BIO {idx}')
    b=ia.decision_brief('owner',i.id,academic_period_id=p.id)
    assert b['data_quality']['status']=='insufficient_population'
    assert b['data_quality']['unique_active_students'] is None
    assert all(x['value'] is None for x in b['metrics'].values())


def test_a_second_tenant_enrollment_cannot_increase_disclosure_population():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    # Inject a malformed tenant-foreign row referencing the same cohort ID.
    from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
    from uuid import uuid4
    with ia.repo.sf() as s:
        s.add(EnrollmentRow(id=uuid4().hex,institution_id='foreign',cohort_id=cohort.id,
            student_account_id='foreign_student',active=True,created_at=NOW));s.commit()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert b['data_quality']['status']=='insufficient_population'


def test_case_contributor_corruption_is_excluded_from_decision_aggregates():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    # Source projection must not count validated but draft/unpublished results.
    from uuid import uuid4
    with ia.repo.sf() as s:
        gb=GradebookRow(id=uuid4().hex,institution_id=i.id,offering_id=off.id,
            title='Epreuve interne',state='draft',pass_percent=50,row_version=1,
            created_by='owner',created_at=NOW,updated_at=NOW)
        comp=ComponentRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gb.id,
            title='Epreuve',kind='exam',weight_percent=100,max_score=20,
            source_assignment_id=None,position=1,created_at=NOW)
        s.add_all([gb,comp]);s.flush()
        for stu in ('student','s2','s3'):
            s.add(MarkRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gb.id,
              component_id=comp.id,student_account_id=stu,score=20,state='validated',
              source_ref=None,validated_by='owner',row_version=1,created_at=NOW,updated_at=NOW,
              attendance='present',note=None))
        s.commit()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert b['metrics']['results.pass_rate']['value'] is None
    assert b['metrics']['results.pass_rate']['denominator'] is None
    with ia.repo.sf() as s:
        row=s.get(GradebookRow,gb.id);row.state='published';s.commit()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert b['metrics']['results.pass_rate']['value']==100.0
    assert b['metrics']['results.pass_rate']['denominator']==3


def test_foreign_and_unenrolled_gradebook_marks_cannot_inflate_results():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    from uuid import uuid4
    with ia.repo.sf() as s:
        gb=GradebookRow(id=uuid4().hex,institution_id=i.id,offering_id=off.id,title='Examen',
            state='published',pass_percent=50,row_version=1,created_by='owner',created_at=NOW,updated_at=NOW)
        comp=ComponentRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gb.id,title='E',kind='exam',
            weight_percent=100,max_score=20,source_assignment_id=None,position=1,created_at=NOW)
        s.add_all([gb,comp]);s.flush()
        for stu,institution in [('student',i.id),('s2',i.id),('outsider',i.id),('s3','foreign')]:
            s.add(MarkRow(id=uuid4().hex,institution_id=institution,gradebook_id=gb.id,
                component_id=comp.id,student_account_id=stu,score=20,state='validated',
                source_ref=None,validated_by='owner',row_version=1,
                created_at=NOW,updated_at=NOW,attendance='present',note=None))
        s.commit()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    # Only two legitimate validated grades, so the result metric is suppressed.
    assert b['metrics']['results.pass_rate']['value'] is None
    assert b['metrics']['results.pass_rate']['status']=='suppressed_small_population'
    assert b['metrics']['results.pass_rate']['denominator'] is None


def test_observatory_is_read_only_and_does_not_create_snapshots():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert ia.history('owner',i.id,scope_type='offering',scope_id=off.id)==()
    assert b['policy']['private_learning_data_used'] is False
    assert b['data_quality']['limitations']


def test_router_declares_authenticated_decision_brief():
    from app.modules.institutional_analytics.api.router import router
    routes=[r for r in router.routes if r.path.endswith('/intelligence/decision-brief')]
    assert len(routes)==1
    assert 'GET' in routes[0].methods
    assert any(x.call.__name__=='current_auth' for x in routes[0].dependant.dependencies)


def test_repeated_attendance_of_one_person_never_counts_as_three_contributors():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    from uuid import uuid4
    with ia.repo.sf() as s:
        for idx in range(3):
            asid=uuid4().hex
            s.add(AttendanceSessionRow(id=asid,institution_id=i.id,
                teaching_session_id=uuid4().hex,offering_id=off.id,state='closed',
                opens_at=NOW,closes_at=NOW+timedelta(hours=1),qr_epoch=0,row_version=1,
                created_by='teacher',created_at=NOW,updated_at=NOW))
            s.add(AttendanceRecordRow(id=uuid4().hex,institution_id=i.id,
                attendance_session_id=asid,student_account_id='student',status='present',
                recorded_at=NOW,method='manual',device_id=None,risk_score=0,review='clear',
                evidence='',row_version=1,updated_at=NOW))
        s.commit()
    b=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert b['metrics']['attendance.attendance_rate']['value'] is None
    assert b['metrics']['attendance.attendance_rate']['denominator'] is None


def test_three_gradebooks_for_one_learner_do_not_publish_a_personal_pass_rate():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    from uuid import uuid4
    with ia.repo.sf() as s:
        pass
    for idx in range(3):
        offering=off if idx==0 else ts.create_offering('owner',i.id,
            course_id=off.course_id,cohort_id=cohort.id,academic_period_id=p.id,label=f'Extra {idx}')
        with ia.repo.sf() as s:
            gb=GradebookRow(id=uuid4().hex,institution_id=i.id,offering_id=offering.id,title='Examen',
                state='published',pass_percent=50,row_version=1,created_by='owner',
                created_at=NOW,updated_at=NOW)
            component=ComponentRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gb.id,title='Examen',
                kind='exam',weight_percent=100,max_score=20,source_assignment_id=None,
                position=1,created_at=NOW)
            mark=MarkRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gb.id,
                component_id=component.id,student_account_id='student',score=20,state='validated',
                source_ref=None,validated_by='owner',row_version=1,created_at=NOW,
                updated_at=NOW,attendance='present',note=None)
            s.add_all([gb,component,mark]);s.commit()
    brief=ia.decision_brief('owner',i.id,academic_period_id=p.id)
    assert brief['data_quality']['unique_active_students']==3
    assert brief['metrics']['results.pass_rate']['value'] is None
    assert brief['metrics']['results.pass_rate']['denominator'] is None
