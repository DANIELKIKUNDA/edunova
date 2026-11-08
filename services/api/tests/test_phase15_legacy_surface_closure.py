"""EduNova 0.50.5: direct public Lot-27 endpoints cannot bypass Phase-15 privacy.

These tests explicitly replace the original unsafe Lot-27 small-cell contract.
The records remain in SQL: their disclosure contract, not the raw data, changes.
"""
import csv
import io
from uuid import uuid4

import pytest

from app.modules.campus.domain.model import CampusRole, UnitKind
from app.modules.institutional_analytics.api.router import router
from test_institutional_analytics_lot27 import seed
from test_phase15_institutional_intelligence import _add_students
from test_phase15_peer_cohort_privacy import _scenario
from test_phase15_source_lineage_completeness import _gradebook


def test_small_cohort_closes_dashboard_signals_csv_and_executive_report():
    _, _, _, _, _, ia, i, p, co, off = seed()
    dashboard = ia.dashboard('owner', i.id, offering_id=off.id)
    assert dashboard['privacy']['status'] == 'insufficient_population'
    assert dashboard['population']['active_enrollments'] is None
    for section in ('teaching', 'attendance', 'assignments', 'results'):
        assert all(value is None for value in dashboard[section].values())
    assert ia.signals('owner', i.id, offering_id=off.id) == ()
    exported = ia.export_csv('owner', i.id, offering_id=off.id)
    rows = list(csv.DictReader(io.StringIO(exported)))
    assert all(row['value'] == '' for row in rows)
    report = ia.executive_report('owner', i.id, offering_id=off.id)
    assert report['kpis']['results']['pass_rate'] is None
    assert report['pedagogical_intelligence']['assessment']['attempts'] is None
    assert report['signals'] == []


def test_bloom_and_assessment_legacy_source_fail_closed_even_if_cohort_is_large():
    cs, _, _, _, _, ia, i, _, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    ped = ia.pedagogical_intelligence('owner', i.id, offering_id=off.id)
    assert ped['privacy']['status'] == 'unverified_legacy_lineage'
    assert ped['assessment'] == {'attempts': None, 'average_percent': None,
                                 'pass_rate': None, 'by_bloom': {}}
    assert all(value is None for value in ped['knowledge_graph'].values())


def test_published_valid_gradebook_can_still_release_governed_aggregate():
    cs, _, _, _, _, ia, i, _, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    _gradebook(ia, i, off, ['student', 'a2', 'a3', 'a4', 'a5'])
    b = ia.dashboard('owner', i.id, offering_id=off.id)
    assert b['privacy']['status'] == 'eligible'
    assert b['results']['pass_rate'] == 100.0
    assert b['results']['complete_results'] == 5
    assert b['results']['passed'] is None  # narrower counter never leaked
    exported = ia.export_csv('owner', i.id, offering_id=off.id)
    assert 'results,pass_rate,100.0' in exported
    assert 'results,passed,' in exported


@pytest.mark.parametrize('location', ['offering','cohort'])
def test_peer_cohort_overlap_suppressed_in_legacy_json_and_csv(location):
    _, _, ia, i, p, co, off, peer, peer_off = _scenario(['student', 'a2', 'a3', 'a4', 'b1'])
    kw = {f'{location}_id':off.id if location == 'offering' else co.id}
    d = ia.dashboard('owner', i.id, academic_period_id=p.id, **kw)
    assert d['privacy']['status'] == 'overlapping_scope_suppressed'
    assert d['results']['pass_rate'] is None
    assert d['population']['active_enrollments'] is None
    assert ia.signals('owner', i.id, academic_period_id=p.id, **kw) == ()
    exported = ia.export_csv('owner', i.id, academic_period_id=p.id, **kw)
    assert all(r['value'] == '' for r in csv.DictReader(io.StringIO(exported)))
    assert ia.executive_report('owner', i.id, academic_period_id=p.id, **kw)['kpis']['results']['complete_results'] is None


def test_tiny_complement_across_hierarchy_suppresses_legacy_unit():
    from test_phase15_hierarchical_privacy_executive import _sibling
    cs, ts, _, _, _, ia, i, p, co, off = seed()
    _add_students(cs,i.id,co.id,'a2','a3','a4','a5')
    # An additional peer differs by just one, inside the requested unit.
    _sibling(cs,ts,i,p,co,off,['student','a2','a3','a4','a5','b1'])
    outside=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Outside',code='OUT',parent_id=None)
    co_out=cs.create_cohort('owner',i.id,program_unit_id=outside.id,
                            academic_period_id=p.id,name='Outside',level='1')
    ts.create_offering('owner',i.id,course_id=off.course_id,
                       cohort_id=co_out.id,academic_period_id=p.id,label='Outside')
    _add_students(cs,i.id,co_out.id,'c1','c2','c3','c4','c5')
    unit=ia.unit_dashboard('owner', i.id, co.program_unit_id, academic_period_id=p.id)
    assert unit['privacy']['status']=='overlapping_scope_suppressed'
    assert unit['results']['pass_rate'] is None


def test_old_v1_snapshot_is_tombstoned_even_with_current_safe_cohort():
    cs, _, _, _, _, ia, i, p, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    secret={'institution_id':i.id,'results':{'pass_rate':100,'complete_results':1},
            'population':{'active_enrollments':1},'student_secret':'PRIVATE'}
    ia.repo.save_immutable_snapshot(i.id, secret, 'offering', off.id, p.id)
    history=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
    assert len(history)==1
    assert history[0]['payload'] is None
    assert history[0]['content_sha256'] is None
    assert history[0]['privacy_status']=='legacy_unverified_snapshot'
    assert 'PRIVATE' not in str(history)


def test_version5_archive_first_only_prevents_temporal_differencing():
    cs, _, _, _, _, ia, i, p, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    _gradebook(ia, i, off, ['student','a2','a3','a4','a5'])
    kw={'academic_period_id':p.id,'offering_id':off.id}
    a=ia.capture_snapshot('owner',i.id,**kw)
    b=ia.capture_snapshot('owner',i.id,**kw)
    assert a['metric_contract_version']==5 and b['metric_contract_version']==5
    history=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
    assert len(history)==2 and history[0]['privacy_status']=='historical_temporal_suppressed'
    assert history[1]['privacy_status']=='governed_current_archive'
    assert history[0]['payload'] is None and history[0]['content_sha256'] is None
    assert history[1]['payload']['results']['pass_rate']==100
    comparison=ia.compare_snapshots('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
    assert comparison['available'] is False and comparison['reason']=='unverified_or_privacy_suppressed_snapshots'


def test_even_version3_archive_is_hidden_if_enrollment_later_becomes_unsafe():
    cs, _, _, _, _, ia, i, p, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    ia.capture_snapshot('owner',i.id,offering_id=off.id)
    with ia.repo.sf() as session:
        from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
        from sqlalchemy import select
        for row in session.scalars(select(EnrollmentRow).where(
                EnrollmentRow.institution_id==i.id,EnrollmentRow.cohort_id==co.id)):
            if row.student_account_id not in ('student','a2'):
                row.active=False
        session.commit()
    history=ia.history('owner',i.id,scope_type='offering',scope_id=off.id)
    assert history[0]['payload'] is None
    assert history[0]['content_sha256'] is None
    assert history[0]['privacy_status']=='current_scope_suppressed'


@pytest.mark.parametrize('scope_type,scope_id',[
    ('wrong','a'),('offering',None),('cohort',None),('academic_unit',None),
    ('institution','nonempty')])
def test_snapshot_history_rejects_wildcard_and_invalid_scopes(scope_type,scope_id):
    _,_,_,_,_,ia,i,_,_,_=seed()
    with pytest.raises(ValueError,match='invalid_snapshot_scope'):
        ia.history('owner',i.id,scope_type=scope_type,scope_id=scope_id)


def test_snapshot_capture_rejects_ambiguous_scope():
    _,_,_,_,_,ia,i,p,co,off=seed()
    with pytest.raises(ValueError,match='ambiguous_snapshot_scope'):
        ia.capture_snapshot('owner',i.id,academic_period_id=p.id,
                            cohort_id=co.id,offering_id=off.id)


def test_faculty_admin_cannot_query_global_or_sibling_legacy_surfaces():
    cs,_,_,_,_,ia,i,p,co,off=seed()
    a=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='A',code='A',parent_id=None)
    b=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='B',code='B',parent_id=None)
    cs.invite_member('owner',i.id,account_id='faculty',role=CampusRole.FACULTY_ADMIN,unit_id=a.id)
    cs.accept_invitation('faculty',i.id)
    for thunk in (
        lambda: ia.dashboard('faculty',i.id),
        lambda: ia.signals('faculty',i.id),
        lambda: ia.export_csv('faculty',i.id),
        lambda: ia.pedagogical_intelligence('faculty',i.id),
        lambda: ia.executive_report('faculty',i.id),
        lambda: ia.history('faculty',i.id,scope_type='institution'),
        lambda: ia.capture_snapshot('faculty',i.id),
        lambda: ia.unit_dashboard('faculty',i.id,b.id),
        lambda: ia.export_csv('faculty',i.id,academic_unit_id=b.id),
    ):
        with pytest.raises(PermissionError):thunk()
    assert ia.unit_dashboard('faculty',i.id,a.id)['scope']['academic_unit_id']==a.id


def test_teacher_can_only_use_their_offering_not_global_unit_or_peer():
    cs,ts,_,_,_,ia,i,p,co,off=seed()
    for fn in (
        lambda:ia.dashboard('teacher',i.id),
        lambda:ia.history('teacher',i.id,scope_type='institution'),
        lambda:ia.capture_snapshot('teacher',i.id),
        lambda:ia.export_csv('teacher',i.id,academic_unit_id=co.program_unit_id),
        lambda:ia.unit_dashboard('teacher',i.id,co.program_unit_id),
    ):
        with pytest.raises(PermissionError):fn()
    assert ia.dashboard('teacher',i.id,offering_id=off.id)['privacy']['status']=='insufficient_population'
    with pytest.raises(ValueError,match='scope_mismatch'):
        ia.dashboard('teacher',i.id,offering_id=off.id,academic_period_id='fake-period')


def test_student_and_foreign_university_cannot_see_archived_records_or_exports():
    cs,_,_,_,_,ia,i,p,co,off=seed()
    alien=cs.create_institution('other-owner',name='Other',slug='other-505',legal_name='',
                                country_code='CD',city='Goma',logo_url=None)
    for actor in ('student','other-owner'):
        for operation in (
            lambda:ia.export_csv(actor,i.id,offering_id=off.id),
            lambda:ia.history(actor,i.id,scope_type='offering',scope_id=off.id),
            lambda:ia.compare_snapshots(actor,i.id,scope_type='offering',scope_id=off.id),
            lambda:ia.executive_report(actor,i.id,offering_id=off.id),
        ):
            with pytest.raises(PermissionError):operation()


def test_legacy_http_routes_all_require_authenticated_context():
    endpoints=('dashboard','signals','export.csv','executive-report','pedagogical-intelligence',
               'snapshots','comparisons','units/{unit_id}/dashboard')
    for name in endpoints:
        route=[r for r in router.routes if r.path.endswith('/'+name)]
        assert route, name
        for item in route:
            assert any(d.call.__name__=='current_auth' for d in item.dependant.dependencies)


def test_real_fastapi_legacy_routes_enforce_masking_and_http_rbac(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.modules.identity.api.router import current_auth
    from app.modules.identity.application.auth_context import AuthContext
    from app.runtime import runtime
    # TestClient executes endpoints on another thread. Share ONE in-memory DB
    # connection rather than letting each SQLite thread create a fresh schema.
    from sqlalchemy import create_engine as _engine
    from sqlalchemy.pool import StaticPool
    import test_institutional_analytics_lot27 as lot27
    monkeypatch.setattr(lot27, 'create_engine', lambda url: _engine(url,
        connect_args={'check_same_thread':False}, poolclass=StaticPool))
    _,_,_,_,_,ia,i,p,co,off=seed()
    monkeypatch.setattr(runtime,'institutional_analytics',ia)
    app=FastAPI()
    app.include_router(router)
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='owner')
    url=f'/institutions/{i.id}'
    with TestClient(app) as client:
        r=client.get(url+'/dashboard',params={'offering_id':off.id})
        assert r.status_code==200 and r.json()['results']['pass_rate'] is None
        r=client.get(url+'/export.csv',params={'offering_id':off.id})
        assert r.status_code==200 and 'results,pass_rate,\r\n' in r.text
        assert 'results,pass_rate,100' not in r.text
        r=client.get(url+'/snapshots',params={'scope_type':'offering'})
        assert r.status_code==422
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student')
        assert client.get(url+'/dashboard',params={'offering_id':off.id}).status_code==403
        assert client.get(url+'/export.csv',params={'offering_id':off.id}).status_code==403
        assert client.get(url+'/snapshots',params={'scope_type':'offering','scope_id':off.id}).status_code==403


def test_real_fastapi_historical_snapshot_never_returns_pre_governance_payload(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.modules.identity.api.router import current_auth
    from app.modules.identity.application.auth_context import AuthContext
    from app.runtime import runtime
    from sqlalchemy import create_engine as _engine
    from sqlalchemy.pool import StaticPool
    import test_institutional_analytics_lot27 as lot27
    monkeypatch.setattr(lot27, 'create_engine', lambda url: _engine(url,
        connect_args={'check_same_thread':False}, poolclass=StaticPool))
    cs,_,_,_,_,ia,i,p,co,off=seed()
    _add_students(cs,i.id,co.id,'a2','a3','a4','a5')
    ia.repo.save_immutable_snapshot(i.id,{'student_secret':'DO_NOT_RELEASE'},'offering',off.id,p.id)
    monkeypatch.setattr(runtime,'institutional_analytics',ia)
    app=FastAPI()
    app.include_router(router)
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='owner')
    with TestClient(app) as client:
        response=client.get(f'/institutions/{i.id}/snapshots',
            params={'scope_type':'offering','scope_id':off.id,'academic_period_id':p.id})
        assert response.status_code==200
        assert response.json()['items'][0]['payload'] is None
        assert 'DO_NOT_RELEASE' not in response.text
        assert response.json()['items'][0]['content_sha256'] is None
