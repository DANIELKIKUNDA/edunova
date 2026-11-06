"""v0.50.3 — static nested difference suppression and executive decision readout.

SQLAlchemy real repository + SQLite test; cross-query privacy is NOT formally proven.
"""
from datetime import timedelta
import pytest

from app.modules.campus.domain.model import CampusRole, PeriodKind, UnitKind
from app.modules.institutional_analytics.api.router import router
from test_institutional_analytics_lot27 import seed, NOW
from test_phase15_institutional_intelligence import _add_students
from test_phase15_source_lineage_completeness import _gradebook


def _sibling(cs, ts, i, p, cohort, off, names):
    sibling=cs.create_cohort('owner',i.id,program_unit_id=cohort.program_unit_id,
        academic_period_id=p.id,name='SECOND',level='2')
    sibling_off=ts.create_offering('owner',i.id,course_id=off.course_id,
        cohort_id=sibling.id,academic_period_id=p.id,label='Second section')
    for n in names:
        if not cs.repo.membership(i.id,n):
            cs.invite_member('owner',i.id,account_id=n,role=CampusRole.STUDENT,unit_id=None)
            cs.accept_invitation(n,i.id)
        cs.enroll('owner',i.id,cohort_id=sibling.id,student_account_id=n)
    return sibling,sibling_off


def test_nested_cohort_and_offering_suppress_small_complement_but_parent_stays_eligible():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'])
    _sibling(cs,ts,i,p,cohort,off,['student','s2','s3','s4'])
    # Parent contains four distinct people; cohort has three.
    parent=ia.decision_brief('owner',i.id,academic_period_id=p.id)
    assert parent['data_quality']['unique_active_students']==4
    for scope in (dict(cohort_id=cohort.id),dict(offering_id=off.id)):
        brief=ia.decision_brief('owner',i.id,academic_period_id=p.id,**scope)
        assert brief['data_quality']['status']=='nested_difference_suppressed'
        assert brief['data_quality']['unique_active_students'] is None
        assert not brief['findings']
        for m in brief['metrics'].values():
            assert m['value'] is None and m['denominator'] is None
            assert m['source_fingerprint_sha256'] is None
            assert m['population_reach']['percent'] is None
            assert m['status']=='suppressed_nested_difference'
        assert 's4' not in str(brief)


def test_three_person_complement_is_disclosable_where_original_metric_passes_other_guards():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'])
    # Different population of three in same period, without overlap.
    sibling=cs.create_cohort('owner',i.id,program_unit_id=cohort.program_unit_id,
        academic_period_id=p.id,name='OTHER',level='2')
    ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=sibling.id,
        academic_period_id=p.id,label='Other offering')
    _add_students(cs,i.id,sibling.id,'t1','t2','t3')
    b=ia.decision_brief('owner',i.id,offering_id=off.id,academic_period_id=p.id)
    assert b['data_quality']['unique_active_students']==3
    assert b['metrics']['results.pass_rate']['status']=='available'
    assert b['metrics']['results.pass_rate']['value']==100


def test_duplicate_membership_not_mistaken_for_a_one_student_complement():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'])
    _sibling(cs,ts,i,p,cohort,off,['student','s2','s3'])
    b=ia.decision_brief('owner',i.id,offering_id=off.id,academic_period_id=p.id)
    assert b['data_quality']['unique_active_students']==3
    assert b['metrics']['results.pass_rate']['value']==100


def test_other_period_has_no_effect_on_scoped_period_or_offering_privacy_guard():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'])
    year=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2030',
        starts_on=NOW.date()+timedelta(days=400),ends_on=NOW.date()+timedelta(days=720),parent_id=None)
    p2=cs.add_period('owner',i.id,kind=PeriodKind.SEMESTER,name='2030 S1',
        starts_on=NOW.date()+timedelta(days=400),ends_on=NOW.date()+timedelta(days=500),parent_id=year.id)
    future=cs.create_cohort('owner',i.id,program_unit_id=cohort.program_unit_id,
        academic_period_id=p2.id,name='NEXT',level='3')
    ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=future.id,
        academic_period_id=p2.id,label='New semester')
    _add_students(cs,i.id,future.id,'f1','f2')
    # Explicit period and implicit period from offering both stay isolated.
    for scope in (dict(offering_id=off.id),dict(offering_id=off.id,academic_period_id=p.id)):
        b=ia.decision_brief('owner',i.id,**scope)
        assert b['metrics']['results.pass_rate']['value']==100


def test_an_unreliable_parent_population_fails_closed(monkeypatch):
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    original=ia.repo.distinct_active_students
    def corrupted(iid,period=None,cohort_id=None,offering_id=None,unit_id=None):
        if not (cohort_id or offering_id or unit_id):return 1
        return original(iid,period,cohort_id,offering_id,unit_id)
    monkeypatch.setattr(ia.repo,'distinct_active_students',corrupted)
    b=ia.decision_brief('owner',i.id,offering_id=off.id,academic_period_id=p.id)
    assert b['data_quality']['status']=='nested_difference_suppressed'
    assert all(m['value'] is None for m in b['metrics'].values())


def test_executive_readout_contains_only_released_governed_metrics_and_human_actions():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'],scores={'student':0,'s2':0,'s3':0})
    readout=ia.executive_readout('owner',i.id,offering_id=off.id)
    result=next(x for x in readout['indicators'] if x['metric']=='results.pass_rate')
    assert result['observed_percent']==0 and result['status']=='available'
    assert result['source_fingerprint_sha256']
    assert any(x['metric']=='results.pass_rate' and x['requires_human_review'] for x in readout['priorities'])
    assert readout['policy']['automatic_decision'] is False
    assert readout['policy']['direct_student_identifiers_exposed'] is False
    assert readout['quality']['metric_count']==5
    assert 'score' not in str(readout).lower()
    assert 'student' not in str(readout['indicators']).lower()
    assert 'student' not in str(readout['priorities']).lower()
    assert all('denominator' not in x for x in readout['indicators'])


def test_executive_readout_cannot_resurrect_suppressed_nested_cells():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'],scores={'student':0,'s2':0,'s3':0})
    _sibling(cs,ts,i,p,cohort,off,['one'])
    result=ia.executive_readout('owner',i.id,offering_id=off.id,academic_period_id=p.id)
    assert result['quality']['status']=='nested_difference_suppressed'
    assert result['priorities']==[]
    assert all(x['observed_percent'] is None and x['source_fingerprint_sha256'] is None
               for x in result['indicators'])


def test_executive_readout_enforces_scope_and_cross_tenant_permissions():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    outsider=cs.create_institution('alien',name='Other University',slug='other-0503',
        legal_name='',country_code='CD',city='Goma',logo_url=None)
    for actor,iid,scope in [('student',i.id,{}),('teacher',i.id,dict(offering_id=off.id)),
                            ('alien',i.id,{}),('owner',outsider.id,{})]:
        with pytest.raises(PermissionError):ia.executive_readout(actor,iid,**scope)
    with pytest.raises(ValueError,match='offering_not_found'):
        ia.executive_readout('owner',i.id,offering_id='foreign')


def test_executive_route_registered():
    assert any(getattr(r,'path',None)=='/institutions/{iid}/intelligence/executive-readout'
               and 'GET' in getattr(r,'methods',set()) for r in router.routes)


def test_faculty_subtree_complement_protected_without_cross_scope_access():
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    faculty=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Health',code='HLT',parent_id=None)
    program=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Chemistry',code='CHE',parent_id=faculty.id)
    new=cs.create_cohort('owner',i.id,program_unit_id=program.id,academic_period_id=p.id,
                         name='CHE1',level='1')
    ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=new.id,
                       academic_period_id=p.id,label='Chemistry 1')
    _add_students(cs,i.id,new.id,'a','b','c')
    cs.invite_member('owner',i.id,account_id='faculty-analyst',role=CampusRole.FACULTY_ADMIN,
                     unit_id=faculty.id)
    cs.accept_invitation('faculty-analyst',i.id)
    guarded=ia.decision_brief('faculty-analyst',i.id,academic_period_id=p.id,
                              academic_unit_id=faculty.id)
    assert guarded['data_quality']['status']=='nested_difference_suppressed'
    assert guarded['data_quality']['unique_active_students'] is None
    assert all(v['value'] is None for v in guarded['metrics'].values())
    with pytest.raises(PermissionError,match='faculty_unit_required'):
        ia.executive_readout('faculty-analyst',i.id)
    with pytest.raises(PermissionError,match='unit_scope_denied'):
        ia.executive_readout('faculty-analyst',i.id,academic_unit_id=cohort.program_unit_id)


def test_executive_readout_router_has_authentication_dependency():
    route=next(r for r in router.routes if r.path.endswith('/intelligence/executive-readout'))
    assert any(dep.call.__name__=='current_auth' for dep in route.dependant.dependencies)
