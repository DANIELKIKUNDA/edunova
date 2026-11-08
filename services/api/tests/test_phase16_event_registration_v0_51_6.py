"""Phase 16: real SQLite SQL + API adversarial event registration tests."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.shared.infrastructure.database import Base
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState
from app.modules.campus_operations.domain.model import CalendarEvent, CalendarEventKind, CalendarEventState
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import SqlAlchemyCampusOperationsRepository
from app.modules.campus_operations.application.service import CampusOperationsService
from app.modules.campus_services.application.service import CampusServicesService
from app.modules.campus_services.infrastructure.event_registration_repo import (
    SqlCampusEventRegistrationRepository, CampusEventRegistrationRow)
from app.modules.campus_services.infrastructure.sqlalchemy_repo import SqlCampusServicesRepository
from app.modules.campus_services.application.event_registration_service import CampusEventRegistrationService
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.main import app
from app.runtime import runtime

NOW = datetime(2026, 10, 23, 8, 30, tzinfo=UTC)

class TenantCampus:
    def __init__(self):
        self.members = {
            ('uni-a', 'admin'): CampusRole.ADMIN,
            ('uni-a', 'student'): CampusRole.STUDENT,
            ('uni-a', 'second'): CampusRole.STUDENT,
            ('uni-a', 'third'): CampusRole.STUDENT,
            ('uni-a', 'teacher'): CampusRole.TEACHER,
            ('uni-a', 'auditor'): CampusRole.AUDITOR,
            ('uni-b', 'admin-b'): CampusRole.ADMIN,
            ('uni-b', 'student-b'): CampusRole.STUDENT,
        }
        self.student_cohorts = {'student': ('c1',), 'second': ('c2',), 'third': ('c1',)}
        self.inactive = set()
    def membership(self, institution, account):
        role = self.members.get((institution, account))
        if role is None:
            return None
        return SimpleNamespace(role=role, state=(MembershipState.REVOKED if (institution, account) in self.inactive else MembershipState.ACTIVE))
    def institution(self, institution):
        return SimpleNamespace(state=InstitutionState.ACTIVE) if institution in ('uni-a','uni-b') else None
    def enrollments_for_student(self, institution, account):
        return [SimpleNamespace(cohort_id=c, active=True) for c in self.student_cohorts.get(account, ())] if institution == 'uni-a' else []

@pytest.fixture
def campus_events():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine, expire_on_commit=False)
    campus = TenantCampus()
    ops_repo = SqlAlchemyCampusOperationsRepository(sf)
    calendar = CampusOperationsService(ops_repo, campus, SimpleNamespace(), lambda: NOW)
    campus_services = CampusServicesService(SqlCampusServicesRepository(sf), campus, lambda: NOW)
    repo = SqlCampusEventRegistrationRepository(sf)
    svc = CampusEventRegistrationService(repo, campus_services, calendar, lambda: NOW)
    yield svc, ops_repo, campus, sf
    engine.dispose()

def event(campus_events, *, institution='uni-a', kind=CalendarEventKind.EVENT,
          state=CalendarEventState.SCHEDULED, cohort=None, starts=None):
    _, ops, _, _ = campus_events
    import uuid
    row = CalendarEvent('cev_'+uuid.uuid4().hex, institution, None, cohort, kind,
                        'Forum scientifique', 'Conférence facultaire',
                        starts or NOW + timedelta(days=7), NOW + timedelta(days=7, hours=2),
                        'Amphithéâtre', state, None, 1, 'admin', NOW, NOW)
    ops.save_event(row)
    return row

def configure(svc, row, cap=2, actor='admin', institution='uni-a', version=1):
    return svc.configure(actor, institution, row.id, version, cap)

def test_legacy_disabled_until_staff_enables_registration(campus_events):
    svc, *_ = campus_events; e = event(campus_events)
    assert svc.list_events('student','uni-a')[0]['registration_capacity'] == 0
    with pytest.raises(ValueError, match='unavailable'): svc.register('student','uni-a',e.id)
    assert configure(svc,e)['registration_capacity'] == 2
    assert svc.register('student','uni-a',e.id)['state'] == 'registered'

def test_capacity_enforced_with_actual_rows(campus_events):
    svc, _, _, sf = campus_events; e = event(campus_events)
    configure(svc,e,2)
    svc.register('student','uni-a',e.id); svc.register('second','uni-a',e.id)
    with pytest.raises(ValueError, match='capacity_conflict'):
        svc.register('third','uni-a',e.id)
    with sf() as db:
        assert len(db.scalars(select(CampusEventRegistrationRow)).all()) == 2

def test_register_duplicate_rejected_and_no_extra_seat(campus_events):
    svc, *_ = campus_events; e = event(campus_events); configure(svc,e,1)
    first=svc.register('student','uni-a',e.id)
    with pytest.raises(ValueError, match='already_registered'):
        svc.register('student','uni-a',e.id)
    assert svc.list_events('student','uni-a')[0]['registrations_count'] == 1
    assert svc.my_registrations('student','uni-a')[0]['id'] == first['id']

def test_withdraw_frees_capacity_and_version_protects_replay(campus_events):
    svc, *_ = campus_events; e=event(campus_events); configure(svc,e,1)
    first=svc.register('student','uni-a',e.id)
    withdrawn=svc.cancel('student','uni-a',e.id,first['row_version'])
    assert withdrawn['row_version']==2 and withdrawn['state']=='cancelled'
    with pytest.raises(ValueError,match='concurrent_conflict'):
        svc.cancel('student','uni-a',e.id,first['row_version'])
    svc.register('second','uni-a',e.id)
    with pytest.raises(ValueError,match='capacity_conflict'):
        svc.register('student','uni-a',e.id)

def test_rejoin_after_cancel_reuses_registration_id_not_duplicates(campus_events):
    svc, *_ = campus_events; e=event(campus_events); configure(svc,e,1)
    r=svc.register('student','uni-a',e.id)
    svc.cancel('student','uni-a',e.id,1)
    restored=svc.register('student','uni-a',e.id)
    assert restored['id']==r['id'] and restored['row_version']==3

def test_capacity_cannot_shrink_below_occupied_and_needs_current_version(campus_events):
    svc, *_=campus_events; e=event(campus_events)
    config=configure(svc,e,3)
    svc.register('student','uni-a',e.id)
    svc.register('second','uni-a',e.id)
    with pytest.raises(ValueError,match='capacity_conflict'):
        configure(svc,e,1,version=config['row_version'])
    with pytest.raises(ValueError,match='concurrent_conflict'):
        configure(svc,e,4,version=1)
    assert configure(svc,e,2,version=2)['registration_capacity']==2

def test_non_event_cannot_be_configured_or_registered(campus_events):
    svc, *_=campus_events; e=event(campus_events,kind=CalendarEventKind.EXAM)
    with pytest.raises(ValueError,match='unavailable'):configure(svc,e,5)
    with pytest.raises(ValueError,match='unavailable'):svc.register('student','uni-a',e.id)

def test_event_cancelled_cannot_register_but_can_withdraw(campus_events):
    svc, ops, _, _=campus_events; e=event(campus_events); configure(svc,e,2)
    r=svc.register('student','uni-a',e.id)
    svc.calendar.update_event_state('admin','uni-a',e.id,'cancelled','Raison vérifiée',2)
    with pytest.raises(ValueError,match='unavailable'):svc.register('second','uni-a',e.id)
    assert svc.cancel('student','uni-a',e.id,r['row_version'])['state']=='cancelled'

def test_past_event_disabled_even_if_legacy_capacity_set(campus_events):
    svc, ops, _, sf=campus_events
    e=event(campus_events, starts=NOW - timedelta(days=1))
    with pytest.raises(ValueError,match='unavailable'):configure(svc,e,2)
    with sf.begin() as db:
        from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow
        db.get(CalendarEventRow,e.id).registration_capacity=2
    with pytest.raises(ValueError,match='unavailable'):svc.register('student','uni-a',e.id)

def test_cross_university_boundaries_and_no_id_discovery(campus_events):
    svc, *_=campus_events; e=event(campus_events);configure(svc,e)
    with pytest.raises(PermissionError,match='membership'):
        svc.register('student-b','uni-a',e.id)
    with pytest.raises(ValueError,match='not_found'):
        svc.register('student-b','uni-b',e.id)
    with pytest.raises(ValueError,match='not_found'):
        configure(svc,e,1,'admin-b','uni-b')
    assert svc.list_events('student-b','uni-b') == []
    assert svc.my_registrations('student-b','uni-b')==[]

def test_cohort_visibility_for_students_enforced_on_registration(campus_events):
    svc,*_=campus_events; e=event(campus_events, cohort='c1'); configure(svc,e)
    with pytest.raises(ValueError,match='not_found'):
        svc.register('second','uni-a',e.id)
    assert svc.register('student','uni-a',e.id)['state']=='registered'
    assert svc.list_events('second','uni-a')==[]

def test_revoked_membership_denied_on_each_request(campus_events):
    svc,_,campus,_=campus_events; e=event(campus_events);configure(svc,e)
    r=svc.register('student','uni-a',e.id)
    campus.inactive.add(('uni-a','student'))
    with pytest.raises(PermissionError):svc.list_events('student','uni-a')
    with pytest.raises(PermissionError):svc.my_registrations('student','uni-a')
    with pytest.raises(PermissionError):svc.cancel('student','uni-a',e.id,r['row_version'])

def test_auditor_cannot_enroll_or_configure(campus_events):
    svc,*_=campus_events; e=event(campus_events);configure(svc,e)
    with pytest.raises(PermissionError,match='read_only'):svc.register('auditor','uni-a',e.id)
    with pytest.raises(PermissionError,match='administrator'):configure(svc,e,3,'auditor')

def test_non_admin_cannot_configure(campus_events):
    svc,*_=campus_events; e=event(campus_events)
    with pytest.raises(PermissionError,match='administrator'):configure(svc,e,5,'teacher')

def test_cannot_cancel_another_members_registration(campus_events):
    svc,*_=campus_events; e=event(campus_events);configure(svc,e,2)
    svc.register('student','uni-a',e.id)
    with pytest.raises(ValueError,match='not_found'):svc.cancel('second','uni-a',e.id,1)

def test_very_large_capacity_and_bool_version_rejected(campus_events):
    svc,*_=campus_events; e=event(campus_events)
    for bad in (-1,5001,True):
        with pytest.raises(ValueError,match='capacity_invalid'):configure(svc,e,bad)
    with pytest.raises(ValueError,match='version_invalid'):configure(svc,e,1,version=True)

def test_api_identity_bound_read_write_and_403_409(campus_events):
    svc,*_=campus_events; e=event(campus_events)
    original=runtime.campus_events
    runtime.campus_events=svc
    try:
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='admin')
        c=TestClient(app)
        url='/v1/campus-services/institutions/uni-a/events'
        assert c.get(url).status_code==200
        assert c.put(url+f'/{e.id}/capacity',json={'capacity':1,'expected_version':1}).status_code==200
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student')
        mine=c.post(url+f'/{e.id}/register')
        assert mine.status_code==200,mine.text
        assert c.post(url+f'/{e.id}/register').status_code==409
        assert c.get(url+'/my-registrations').json()[0]['account_id']=='student'
        assert c.put(url+f'/{e.id}/capacity',json={'capacity':5,'expected_version':2}).status_code==403
        result=c.post(url+f'/{e.id}/withdraw',json={'expected_version':mine.json()['row_version']})
        assert result.status_code==200,result.text
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student-b')
        assert c.get(url).status_code==403
        assert c.post(url+f'/{e.id}/register').status_code==403
    finally:
        app.dependency_overrides.pop(current_auth,None)
        runtime.campus_events=original


def test_http_boolean_capacity_and_versions_cannot_coerce(campus_events):
    svc, *_ = campus_events; e = event(campus_events)
    original = runtime.campus_events
    runtime.campus_events = svc
    app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='admin')
    try:
        c = TestClient(app)
        url = f'/v1/campus-services/institutions/uni-a/events/{e.id}/capacity'
        assert c.put(url, json={'capacity': True, 'expected_version': 1}).status_code == 422
        assert c.put(url, json={'capacity': 2, 'expected_version': True}).status_code == 422
        assert svc.list_events('admin','uni-a')[0]['registration_capacity'] == 0
    finally:
        app.dependency_overrides.pop(current_auth, None)
        runtime.campus_events = original


def test_suspended_university_cannot_publish_or_read_event_registrations(campus_events):
    svc, _, campus, _ = campus_events
    e = event(campus_events)
    configure(svc, e)
    campus.institution = lambda i: SimpleNamespace(state=InstitutionState.SUSPENDED)
    with pytest.raises(PermissionError, match='not_active'):
        svc.list_events('admin', 'uni-a')
    with pytest.raises(PermissionError, match='not_active'):
        svc.register('student', 'uni-a', e.id)
    with pytest.raises(PermissionError, match='not_active'):
        svc.my_registrations('student', 'uni-a')
