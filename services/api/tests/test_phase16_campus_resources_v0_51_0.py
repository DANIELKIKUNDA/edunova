"""Phase 16 foundation: actual SQL repository, HTTP contract, adversarial RBAC."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.shared.infrastructure.database import Base
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState
from app.modules.campus_services.application.service import CampusServicesService
from app.modules.campus_services.infrastructure.sqlalchemy_repo import SqlCampusServicesRepository
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.main import app
from app.runtime import runtime

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=UTC)

class Memberships:
    def __init__(self):
        self.members = {
            ('uni-a', 'admin'): CampusRole.ADMIN,
            ('uni-a', 'student'): CampusRole.STUDENT,
            ('uni-a', 'student2'): CampusRole.STUDENT,
            ('uni-a', 'teacher'): CampusRole.TEACHER,
            ('uni-a', 'faculty'): CampusRole.FACULTY_ADMIN,
            ('uni-a', 'auditor'): CampusRole.AUDITOR,
            ('uni-b', 'admin-b'): CampusRole.OWNER,
            ('uni-b', 'student-b'): CampusRole.STUDENT,
        }
    def institution(self, i):
        return SimpleNamespace(state=InstitutionState.ACTIVE) if i in {'uni-a','uni-b'} else None
    def membership(self, i, a):
        role = self.members.get((i, a))
        return SimpleNamespace(role=role, state=MembershipState.ACTIVE) if role else None

@pytest.fixture
def setup_phase16():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    repo = SqlCampusServicesRepository(sessionmaker(bind=engine, expire_on_commit=False))
    service = CampusServicesService(repo, Memberships(), lambda: NOW)
    yield service
    engine.dispose()

def add(service, institution='uni-a', actor='admin', code='S-01'):
    return service.register_resource(actor, institution, kind='laboratory', code=code,
                                     name='Laboratoire de physique', location='Bloc B', capacity=30)

def book(service, resource, actor='student', institution='uni-a', start=None, end=None):
    start = start or NOW + timedelta(days=1)
    end = end or start + timedelta(hours=2)
    return service.book(actor, institution, resource_id=resource.id, purpose='TP de physique',
                        starts_at=start, ends_at=end)

def test_create_list_book_cancel_and_rebook(setup_phase16):
    svc = setup_phase16
    resource = add(svc)
    assert svc.list_resources('student', 'uni-a')[0].id == resource.id
    first = book(svc, resource)
    assert first.state.value == 'confirmed'
    with pytest.raises(ValueError, match='conflict'):book(svc, resource, actor='student2')
    assert svc.cancel_booking('student', 'uni-a', first.id, 1).state.value == 'cancelled'
    assert book(svc, resource, actor='student2').requested_by == 'student2'

def test_half_open_windows_and_timezone_normalization(setup_phase16):
    svc=setup_phase16; r=add(svc)
    first=book(svc,r)
    second=book(svc,r,actor='student2',start=first.ends_at)
    assert second.starts_at==first.ends_at
    local_start=NOW+timedelta(days=2)
    from datetime import timezone
    off=timezone(timedelta(hours=2))
    shifted=local_start.astimezone(off)
    b=book(svc,r,start=shifted,end=(local_start+timedelta(hours=1)).astimezone(off))
    assert b.starts_at == local_start

def test_cross_tenant_resource_access_denied_and_no_listing(setup_phase16):
    svc=setup_phase16;r=add(svc)
    assert svc.list_resources('student-b','uni-b') == ()
    with pytest.raises(ValueError,match='unavailable'):
        book(svc,r,actor='student-b',institution='uni-b')
    with pytest.raises(PermissionError,match='membership'):
        svc.list_resources('student-b','uni-a')
    with pytest.raises(ValueError,match='not_found'):
        svc.cancel_booking('admin-b','uni-b','bkg_other',1)

def test_student_cannot_register_or_deactivate_resource(setup_phase16):
    svc=setup_phase16;r=add(svc)
    with pytest.raises(PermissionError,match='administrator'):
        add(svc,actor='student',code='S-02')
    with pytest.raises(PermissionError,match='administrator'):
        svc.deactivate_resource('student','uni-a',r.id,1)

def test_auditor_can_list_but_not_book(setup_phase16):
    svc=setup_phase16;r=add(svc)
    assert len(svc.list_resources('auditor','uni-a'))==1
    with pytest.raises(PermissionError,match='read_only'):
        book(svc,r,actor='auditor')

def test_student_reads_only_personal_bookings(setup_phase16):
    svc=setup_phase16;r=add(svc)
    one=book(svc,r)
    two=book(svc,r,actor='student2',start=NOW+timedelta(days=2))
    assert [x.id for x in svc.list_bookings('student','uni-a')]==[one.id]
    assert [x.id for x in svc.list_bookings('faculty','uni-a')]==[]
    assert {x.id for x in svc.list_bookings('admin','uni-a')}=={one.id,two.id}
    with pytest.raises(PermissionError,match='owner'):
        svc.cancel_booking('student2','uni-a',one.id,1)

def test_invalid_windows_and_naive_datetime_rejected(setup_phase16):
    svc=setup_phase16;r=add(svc)
    with pytest.raises(ValueError,match='timezone'):
        book(svc,r,start=datetime(2026,10,21,10),end=datetime(2026,10,21,11))
    with pytest.raises(ValueError,match='window'):
        book(svc,r,start=NOW+timedelta(days=1),end=NOW+timedelta(days=1,hours=9))
    with pytest.raises(ValueError,match='window'):
        book(svc,r,start=NOW-timedelta(days=1),end=NOW)

def test_code_uniqueness_per_tenant_but_not_globally(setup_phase16):
    svc=setup_phase16;add(svc)
    with pytest.raises(ValueError,match='code_already_exists'):
        add(svc,code='s-01')
    assert add(svc,institution='uni-b',actor='admin-b').code=='S-01'

def test_deactivation_version_and_no_future_booking(setup_phase16):
    svc=setup_phase16;r=add(svc)
    with pytest.raises(ValueError,match='concurrent'):
        svc.deactivate_resource('admin','uni-a',r.id,3)
    updated=svc.deactivate_resource('admin','uni-a',r.id,1)
    assert not updated.active and updated.row_version==2
    with pytest.raises(ValueError,match='unavailable'):book(svc,r)

def test_stale_cancel_version_rejected(setup_phase16):
    svc=setup_phase16;r=add(svc);b=book(svc,r)
    svc.cancel_booking('student','uni-a',b.id,1)
    with pytest.raises(ValueError,match='concurrent'):
        svc.cancel_booking('student','uni-a',b.id,1)

def test_api_end_to_end_identity_bound(setup_phase16):
    service=setup_phase16;original=runtime.campus_services
    runtime.campus_services=service
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='admin')
    try:
        client=TestClient(app)
        res=client.post('/v1/campus-services/institutions/uni-a/resources',json={
            'kind':'room','code':'AMPHI','name':'Amphithéâtre','capacity':100})
        assert res.status_code==200,res.text
        resource=res.json();assert resource['kind']=='room'
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student')
        assert client.get('/v1/campus-services/institutions/uni-a/resources').status_code==200
        assert client.post('/v1/campus-services/institutions/uni-a/resources',json={
            'kind':'room','code':'PRIV','name':'Interdit'}).status_code==403
        payload={'resource_id':resource['id'],'purpose':'Séminaire',
                 'starts_at':(NOW+timedelta(days=1)).isoformat(),
                 'ends_at':(NOW+timedelta(days=1,hours=2)).isoformat()}
        booked=client.post('/v1/campus-services/institutions/uni-a/bookings',json=payload)
        assert booked.status_code==200,booked.text
        assert client.post('/v1/campus-services/institutions/uni-a/bookings',json=payload).status_code==409
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student-b')
        assert client.get('/v1/campus-services/institutions/uni-a/bookings').status_code==403
        assert client.get('/v1/campus-services/institutions/uni-b/bookings').json()==[]
    finally:
        app.dependency_overrides.pop(current_auth,None)
        runtime.campus_services=original

def test_revoked_membership_and_suspended_institution_deny_access(setup_phase16):
    svc = setup_phase16
    r = add(svc)
    svc.campus.members.pop(('uni-a', 'student'))
    with pytest.raises(PermissionError, match='membership'):
        book(svc, r)
    svc.campus.members[('uni-a','student')] = CampusRole.STUDENT
    svc.campus.institution = lambda i: SimpleNamespace(state=InstitutionState.SUSPENDED)
    with pytest.raises(PermissionError, match='not_active'):
        svc.list_resources('student','uni-a')
    with pytest.raises(PermissionError, match='not_active'):
        book(svc,r)
