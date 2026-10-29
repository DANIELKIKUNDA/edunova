"""Phase 16: academic resource/calendar integrity + opt-in alumni negative paths."""
from datetime import timedelta
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow
from app.modules.campus_services.application.alumni_service import CampusAlumniService
from app.modules.campus_services.infrastructure.alumni_repo import SqlCampusAlumniRepository
from app.modules.campus_services.infrastructure.sqlalchemy_repo import SqlCampusServicesRepository
from app.modules.campus_services.application.service import CampusServicesService
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from test_phase16_campus_resources_v0_51_0 import Memberships, NOW, setup_phase16, add, book


def event(service, *, institution='uni-a', name='Cours de physique', start=None,
          kind='session', offering='offering-1', state='scheduled'):
    from uuid import uuid4
    start = start or NOW + timedelta(days=1)
    with service.repo.sf.begin() as s:
        id = 'cev_' + uuid4().hex
        s.add(CalendarEventRow(id=id, institution_id=institution, offering_id=offering,
            cohort_id=None, kind=kind, title=name, details='', starts_at=start,
            ends_at=start + timedelta(hours=2), location='Bloc B', state=state,
            source_ref=None, registration_capacity=0, row_version=1,
            created_by='admin', created_at=NOW, updated_at=NOW))
    return id


def test_calendar_allocation_blocks_booking_in_both_directions(setup_phase16):
    s = setup_phase16; r = add(s); eid = event(s)
    assign = s.assign_calendar_resource('admin', 'uni-a', eid, r.id)
    assert assign['calendar_event_id'] == eid
    with pytest.raises(ValueError, match='academic_conflict'):
        book(s, r)
    other = add(s, code='B-02'); b = book(s, other)
    with pytest.raises(ValueError, match='booking_conflict'):
        s.assign_calendar_resource('admin', 'uni-a', event(s, name='Examen'), other.id)
    assert s.cancel_booking('student', 'uni-a', b.id, 1).state.value == 'cancelled'
    assert s.assign_calendar_resource('admin', 'uni-a', event(s), other.id)


def test_calendar_cancel_frees_slot_and_release_checks_version(setup_phase16):
    s = setup_phase16; r = add(s); eid = event(s)
    a = s.assign_calendar_resource('admin', 'uni-a', eid, r.id)
    with s.repo.sf.begin() as db:
        from sqlalchemy import update
        db.execute(update(CalendarEventRow).where(CalendarEventRow.id == eid).values(state='cancelled'))
    assert book(s, r)
    with pytest.raises(ValueError, match='concurrent'):
        s.release_calendar_resource('admin', 'uni-a', a['id'], 4)
    assert s.release_calendar_resource('admin', 'uni-a', a['id'], 1)['released']


def test_assignment_tenant_rbac_and_bad_event(setup_phase16):
    s = setup_phase16; r = add(s); eid = event(s)
    with pytest.raises(PermissionError, match='administrator'):
        s.assign_calendar_resource('student','uni-a',eid,r.id)
    with pytest.raises(PermissionError, match='administrator'):
        s.calendar_allocations('auditor', 'uni-a')
    with pytest.raises(ValueError, match='unavailable'):
        s.assign_calendar_resource('admin-b','uni-b',eid,r.id)
    with pytest.raises(ValueError, match='not_eligible'):
        s.assign_calendar_resource('admin','uni-a','nonexistent',r.id)
    assert not s.calendar_allocations('admin-b','uni-b')
    a = s.assign_calendar_resource('admin','uni-a',eid,r.id)
    with pytest.raises(ValueError, match='already_assigned'):
        s.assign_calendar_resource('admin','uni-a',eid,r.id)
    with pytest.raises(ValueError, match='not_found'):
        s.release_calendar_resource('admin-b','uni-b',a['id'],1)


def test_assignment_maintenance_guard_and_adjacent_times(setup_phase16):
    s = setup_phase16; r = add(s); eid = event(s)
    s.assign_calendar_resource('admin','uni-a',eid,r.id)
    ticket = s.report_maintenance('student','uni-a',r.id,'Lampe défaillante')
    with pytest.raises(ValueError, match='academic_conflict'):
        s.transition_maintenance('admin','uni-a',ticket.id,1,'start')
    assert book(s, r, start=NOW + timedelta(days=1,hours=2),
                end=NOW + timedelta(days=1,hours=3))


def test_session_requires_offering_and_equipment_not_room(setup_phase16):
    s = setup_phase16; r = add(s)
    with pytest.raises(ValueError, match='offering_required'):
        s.assign_calendar_resource('admin','uni-a',event(s,offering=None),r.id)
    eq = s.register_resource('admin','uni-a',kind='equipment',code='EQ1',name='Projecteur')
    with pytest.raises(ValueError, match='kind_invalid'):
        s.assign_calendar_resource('admin','uni-a',event(s),eq.id)


@pytest.fixture
def alumni_services(setup_phase16):
    s = setup_phase16
    repo = SqlCampusAlumniRepository(s.repo.sf)
    campus = Memberships()
    return CampusAlumniService(repo, campus, lambda: NOW), campus


def submit(s, actor='student', institution='uni-a', version=0, visible=True):
    return s.apply(actor,institution,display_name='Marie Alumna',program_name='Médecine',
                   graduation_year=2024,headline='Médecin',visible=visible,
                   expected_version=version)


def test_alumni_consent_published_only_after_staff_validation(alumni_services):
    s,_ = alumni_services
    own = submit(s)
    assert own['status'] == 'pending'
    assert s.directory('teacher','uni-a') == []
    with pytest.raises(PermissionError):
        s.decide('student','uni-a',own['id'],1,'verified','registry-2024')
    with pytest.raises(PermissionError, match='self_verification'):
        own_admin = submit(s,actor='admin')
        s.decide('admin','uni-a',own_admin['id'],1,'verified','registry-2024')
    checked = s.decide('admin','uni-a',own['id'],1,'verified','registry-2024')
    assert checked['status'] == 'verified'
    public = s.directory('teacher','uni-a')
    assert len(public) == 1 and public[0]['display_name'] == 'Marie Alumna'
    assert 'account_id' not in public[0] and 'verification_reference' not in public[0]
    renewed = submit(s,version=2)
    assert renewed['status']=='pending' and s.directory('teacher','uni-a')==[]


def test_alumni_non_consensual_and_rejected_never_public(alumni_services):
    s,_ = alumni_services
    p=submit(s,visible=False)
    s.decide('admin','uni-a',p['id'],1,'verified','registry-2024')
    assert s.directory('student','uni-a') == []
    p=submit(s,version=2,visible=True)
    s.decide('admin','uni-a',p['id'],3,'rejected','record-not-found')
    assert s.directory('student','uni-a') == []


def test_alumni_tenant_isolation_concurrency_and_retired_member(alumni_services):
    s, campus = alumni_services
    p = submit(s)
    with pytest.raises(ValueError, match='concurrent'):
        submit(s,version=0)
    with pytest.raises(ValueError, match='not_found'):
        s.decide('admin-b','uni-b',p['id'],1,'verified','registry')
    s.decide('admin','uni-a',p['id'],1,'verified','registry-2024')
    del campus.members[('uni-a','student')]
    assert s.my_profile('student','uni-a')['status'] == 'verified'
    assert len(s.directory('student','uni-a')) == 1
    with pytest.raises(PermissionError):
        submit(s,version=2)
    with pytest.raises(PermissionError):
        s.directory('student','uni-b')


def test_alumni_opportunity_staff_only_and_no_cross_tenant(alumni_services):
    s,_ = alumni_services
    with pytest.raises(PermissionError):
        s.post_opportunity('student','uni-a','Offre','Un stage de médecine')
    with pytest.raises(ValueError, match='url_invalid'):
        s.post_opportunity('admin','uni-a','Offre','Un stage de médecine','javascript:alert(1)')
    offer = s.post_opportunity('admin','uni-a','Stage médecin','Stage au centre de santé','https://example.org/apply')
    assert len(s.opportunities('student','uni-a')) == 1
    assert s.opportunities('admin-b','uni-b') == []
    with pytest.raises(ValueError, match='concurrent'):
        s.withdraw_opportunity('admin','uni-a',offer['id'],2)
    with pytest.raises(ValueError, match='concurrent'):
        s.withdraw_opportunity('admin-b','uni-b',offer['id'],1)
    s.withdraw_opportunity('admin','uni-a',offer['id'],1)
    assert s.opportunities('student','uni-a')==[]


@pytest.mark.parametrize('bad_url', [
    'https://localhost/apply', 'https://127.0.0.1/apply',
    'https://[::1]/apply', 'https://intranet.local/apply',
    'https://example.org:invalid/apply', 'https://example.org:0/apply',
    'https://example.org/apply#javascript:alert(1)',
    'https://example.org\n.evil.test/apply', 'https://user@example.org/apply',
    'https://example.org:99999/apply',
])
def test_alumni_opportunity_rejects_unsafe_destination(alumni_services, bad_url):
    service, _ = alumni_services
    with pytest.raises(ValueError, match='alumni_opportunity_url_invalid'):
        service.post_opportunity('admin', 'uni-a', 'Stage médecin',
                                 'Stage au centre de santé', bad_url)


def test_alumni_api_authenticated_identity_and_admin_boundary(alumni_services):
    service, _ = alumni_services
    previous = runtime.campus_alumni
    runtime.campus_alumni = service
    app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='student')
    try:
        c = TestClient(app)
        payload=dict(display_name='Etudiant',program_name='Biologie',graduation_year=2024,
            visible=True,expected_version=0)
        result = c.put('/v1/campus-services/institutions/uni-a/alumni/me',json=payload)
        assert result.status_code == 200, result.text
        assert c.get('/v1/campus-services/institutions/uni-a/alumni/pending').status_code==403
        assert c.get('/v1/campus-services/institutions/uni-b/alumni/me').status_code==403
        app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='admin')
        pending = c.get('/v1/campus-services/institutions/uni-a/alumni/pending')
        assert pending.status_code==200 and len(pending.json())==1
        row=pending.json()[0]
        approved=c.post(f'/v1/campus-services/institutions/uni-a/alumni/{row["id"]}/decide',
            json={'expected_version':1,'decision':'verified','reference':'registry2024'})
        assert approved.status_code==200, approved.text
        app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='teacher')
        people=c.get('/v1/campus-services/institutions/uni-a/alumni/directory')
        assert people.status_code==200 and len(people.json())==1
    finally:
        runtime.campus_alumni = previous
        app.dependency_overrides.clear()


def teaching_session(service, institution='uni-a', start=None, state='planned'):
    from app.modules.teaching.infrastructure.sqlalchemy_repo import SessionRow
    from uuid import uuid4
    start = start or NOW + timedelta(days=1)
    with service.repo.sf.begin() as db:
        id = 'ts_'+uuid4().hex
        db.add(SessionRow(id=id, institution_id=institution, offering_id='offering-a',
            title='Séance du cours', starts_at=start, ends_at=start+timedelta(hours=2),
            state=state, summary='', next_topic='', row_version=1,
            created_by='teacher', created_at=NOW, updated_at=NOW))
    return id


def test_teaching_sessions_block_booking_and_calendar(setup_phase16):
    s = setup_phase16; room=add(s)
    ts=teaching_session(s)
    alloc=s.assign_teaching_room('admin','uni-a',ts,room.id)
    assert alloc['teaching_session_id']==ts
    with pytest.raises(ValueError, match='teaching_conflict'):
        book(s,room)
    with pytest.raises(ValueError, match='teaching_conflict'):
        s.assign_calendar_resource('admin','uni-a',event(s),room.id)
    with pytest.raises(ValueError, match='teaching_conflict'):
        s.transition_maintenance('admin','uni-a',s.report_maintenance(
            'student','uni-a',room.id,'Panne de climatisation').id,1,'start')


def test_teaching_assignment_checks_rbac_tenant_and_cancellation(setup_phase16):
    s = setup_phase16; room=add(s)
    ts=teaching_session(s)
    with pytest.raises(PermissionError):
        s.assign_teaching_room('teacher','uni-a',ts,room.id)
    with pytest.raises(ValueError, match='not_eligible'):
        s.assign_teaching_room('admin','uni-a', 'invalid', room.id)
    with pytest.raises(ValueError, match='unavailable'):
        s.assign_teaching_room('admin-b','uni-b',ts,room.id)
    a=s.assign_teaching_room('admin','uni-a',ts,room.id)
    with pytest.raises(ValueError,match='already_assigned'):
        s.assign_teaching_room('admin','uni-a',ts,room.id)
    assert not s.teaching_allocations('admin-b','uni-b')
    with pytest.raises(ValueError,match='not_found'):
        s.release_teaching_room('admin-b','uni-b',a['id'],1)
    with pytest.raises(ValueError,match='concurrent'):
        s.release_teaching_room('admin','uni-a',a['id'],2)
    assert s.release_teaching_room('admin','uni-a',a['id'],1)['released']
    assert book(s,room)


def test_teaching_session_state_change_frees_room_slot(setup_phase16):
    from app.modules.teaching.infrastructure.sqlalchemy_repo import SessionRow
    from sqlalchemy import update
    s=setup_phase16; room=add(s); ts=teaching_session(s)
    s.assign_teaching_room('admin','uni-a',ts,room.id)
    with s.repo.sf.begin() as db:
        db.execute(update(SessionRow).where(SessionRow.id == ts).values(state='cancelled'))
    assert book(s,room)


def test_booking_prevents_teaching_allocation_and_adjacent_allowed(setup_phase16):
    s=setup_phase16;room=add(s);b=book(s,room)
    with pytest.raises(ValueError,match='booking_conflict'):
        s.assign_teaching_room('admin','uni-a',teaching_session(s),room.id)
    assert s.assign_teaching_room('admin','uni-a',teaching_session(
        s,start=NOW+timedelta(days=1,hours=2)),room.id)


def test_explicit_alumni_membership_revocation_overrides_previous_verification(alumni_services):
    from app.modules.campus.domain.model import CampusRole, MembershipState
    s, campus = alumni_services
    profile = submit(s)
    s.decide('admin', 'uni-a', profile['id'], 1, 'verified', 'registry-2024')
    previous = campus.membership
    campus.membership = lambda inst, acct: (
        SimpleNamespace(role=CampusRole.STUDENT, state=MembershipState.REVOKED)
        if (inst, acct) == ('uni-a', 'student') else previous(inst, acct))
    with pytest.raises(PermissionError, match='revoked'):
        s.directory('student', 'uni-a')
    with pytest.raises(PermissionError, match='revoked'):
        s.my_profile('student', 'uni-a')
    with pytest.raises(PermissionError, match='revoked'):
        s.opportunities('student', 'uni-a')
