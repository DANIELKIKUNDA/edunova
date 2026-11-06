"""Adversarial closure: tenant-scoped Alumni discovery and uncovered schedule reporting."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.main import app
from app.runtime import runtime
from app.modules.campus.domain.model import InstitutionState, MembershipState
from app.modules.campus_services.application.alumni_service import CampusAlumniService
from app.modules.campus_services.infrastructure.alumni_repo import SqlCampusAlumniRepository
from app.modules.campus_services.application.service import CampusServicesService
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow
from app.modules.teaching.infrastructure.sqlalchemy_repo import SessionRow
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext

from test_phase16_academic_alumni_v0_51_8 import (
    setup_phase16, event, teaching_session, submit, alumni_services,
)
from test_phase16_campus_resources_v0_51_0 import NOW, add, Memberships


def test_unassigned_schedule_reconciliation_is_not_automatic(setup_phase16):
    service = setup_phase16
    room = add(service)
    event_id = event(service)
    session_id = teaching_session(service)
    report = service.unassigned_academic_sessions('admin', 'uni-a')
    assert report['calendar_count'] == report['teaching_count'] == 1
    assert report['calendar'][0]['id'] == event_id
    assert report['teaching'][0]['id'] == session_id
    assert report['truncated'] is False
    with pytest.raises(PermissionError):
        service.unassigned_academic_sessions('student', 'uni-a')
    with pytest.raises(PermissionError):
        service.unassigned_academic_sessions('admin-b', 'uni-a')
    assert service.unassigned_academic_sessions('admin-b', 'uni-b')['calendar_count'] == 0
    service.assign_calendar_resource('admin', 'uni-a', event_id, room.id)
    report = service.unassigned_academic_sessions('admin', 'uni-a')
    assert report['calendar_count'] == 0 and report['teaching_count'] == 1
    room2 = add(service, code='R-09')
    service.assign_teaching_room('admin', 'uni-a', session_id, room2.id)
    assert service.unassigned_academic_sessions('admin', 'uni-a')['teaching_count'] == 0


def test_report_filters_expired_cancelled_and_uses_deterministic_counts(setup_phase16):
    service = setup_phase16
    event(service, state='cancelled')
    teaching_session(service, state='cancelled')
    event(service, start=NOW - timedelta(days=2))
    teaching_session(service, start=NOW - timedelta(days=2))
    for n in range(4):
        event(service, name=f'Séance {n}')
    report = service.repo.unassigned_academic_sessions('uni-a', NOW, limit=2)
    assert report['calendar_count'] == 4 and len(report['calendar']) == 2
    assert report['teaching_count'] == 0
    assert report['truncated'] is True
    assert not service.repo.unassigned_academic_sessions('uni-b', NOW)['calendar']


def test_alumni_discovery_only_own_verified_not_suspended(alumni_services):
    service, campus = alumni_services
    campus.institution = lambda inst: SimpleNamespace(state=InstitutionState.ACTIVE,
        name=f'Université {inst}') if inst in {'uni-a', 'uni-b'} else None
    assert service.my_institutions('student') == []
    profile = submit(service)
    assert service.my_institutions('student') == []
    service.decide('admin', 'uni-a', profile['id'], 1, 'verified', 'reference-2024')
    assert service.my_institutions('student') == [{'institution_id': 'uni-a', 'name': 'Université uni-a'}]
    assert service.my_institutions('student2') == []
    assert service.my_institutions('admin') == []
    original = campus.membership
    campus.membership = lambda inst, actor: (SimpleNamespace(state=MembershipState.REVOKED)
        if inst == 'uni-a' and actor == 'student' else original(inst, actor))
    assert service.my_institutions('student') == []
    campus.membership = lambda inst, actor: (SimpleNamespace(state=MembershipState.SUSPENDED)
        if inst == 'uni-a' and actor == 'student' else original(inst, actor))
    assert service.my_institutions('student') == []
    campus.membership = lambda inst, actor: None if inst == 'uni-a' and actor == 'student' else original(inst, actor)
    assert service.my_institutions('student')[0]['institution_id'] == 'uni-a'
    assert service.directory('student', 'uni-a')[0]['display_name'] == 'Marie Alumna'
    with pytest.raises(PermissionError):
        service.apply('student', 'uni-a', display_name='New Profile', program_name='Med',
            graduation_year=2024, expected_version=2)


def test_alumni_discovery_hides_inactive_tenant_and_unverified_profiles(alumni_services):
    service, campus = alumni_services
    profile = submit(service)
    service.decide('admin', 'uni-a', profile['id'], 1, 'rejected', 'reference-reject')
    assert service.my_institutions('student') == []
    profile = submit(service, version=2)
    service.decide('admin', 'uni-a', profile['id'], 3, 'verified', 'reference-verify')
    campus.institution = lambda inst: SimpleNamespace(state=InstitutionState.SUSPENDED, name='Non actif')
    assert service.my_institutions('student') == []


def test_new_routes_use_authenticated_principal_only(setup_phase16, alumni_services):
    academic, alumni = setup_phase16, alumni_services[0]
    alumni.campus.institution = lambda inst: SimpleNamespace(state=InstitutionState.ACTIVE,
        name='Université A') if inst == 'uni-a' else None
    previous_academic, previous_alumni = runtime.campus_services, runtime.campus_alumni
    runtime.campus_services, runtime.campus_alumni = academic, alumni
    account = {'id': 'student'}
    app.dependency_overrides[current_auth] = lambda: AuthContext(account_id=account['id'])
    try:
        c = TestClient(app)
        assert c.get('/v1/campus-services/alumni/my-institutions').json() == []
        p = submit(alumni)
        alumni.decide('admin','uni-a',p['id'],1,'verified','reference-tested')
        r = c.get('/v1/campus-services/alumni/my-institutions')
        assert r.status_code == 200 and r.json() == [{'institution_id':'uni-a','name':'Université A'}]
        assert c.get('/v1/campus-services/institutions/uni-a/academic-unassigned').status_code == 403
        account['id']='admin'
        assert c.get('/v1/campus-services/alumni/my-institutions').json() == []
        r = c.get('/v1/campus-services/institutions/uni-a/academic-unassigned')
        assert r.status_code == 200 and r.json()['calendar_count'] == 0
    finally:
        runtime.campus_services, runtime.campus_alumni = previous_academic, previous_alumni
        app.dependency_overrides.clear()
