"""Actual SQL and HTTP maintenance lifecycle, role and tenant adversarial checks."""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus_services.infrastructure.sqlalchemy_repo import CampusMaintenanceRow, CampusBookingRow, CampusResourceRow
from test_phase16_campus_resources_v0_51_0 import setup_phase16, add, book, NOW


def report(svc, resource, actor='student', institution='uni-a'):
    return svc.report_maintenance(actor, institution, resource.id, 'La ressource présente un défaut matériel important.')


def advance(svc, ticket, action, actor='admin', institution='uni-a', note='Réparation contrôlée et vérifiée.'):
    return svc.transition_maintenance(actor, institution, ticket.id, ticket.row_version, action, note)


def test_report_is_non_disruptive_and_visible_to_reporter(setup_phase16):
    svc = setup_phase16; resource = add(svc); ticket = report(svc, resource)
    assert ticket.status.value == 'reported' and ticket.row_version == 1
    assert book(svc, resource).state.value == 'confirmed'
    assert [v.id for v in svc.maintenance_tickets('student','uni-a')] == [ticket.id]


def test_admin_can_start_and_bookings_cancelled_atomically(setup_phase16):
    svc = setup_phase16; resource = add(svc)
    earlier = book(svc,resource, start=NOW + timedelta(days=1))
    later = book(svc,resource, actor='student2', start=NOW + timedelta(days=2))
    ticket = advance(svc, report(svc, resource), 'start')
    assert ticket.status.value == 'in_progress' and ticket.row_version == 2
    assert svc.list_resources('student','uni-a')[0].service_state == 'maintenance'
    by_id = {b.id: b for b in svc.list_bookings('admin','uni-a')}
    assert all(by_id[k].state.value == 'cancelled' and by_id[k].cancellation_reason == 'resource_maintenance'
               and by_id[k].row_version == 2 for k in (earlier.id, later.id))
    assert len(svc.list_bookings('student','uni-a')) == 1
    with pytest.raises(ValueError,match='unavailable'):
        book(svc,resource,start=NOW+timedelta(days=3))


def test_resolve_restores_but_never_resurrects_cancelled_bookings(setup_phase16):
    svc=setup_phase16; r=add(svc); b=book(svc,r)
    t=advance(svc,report(svc,r),'start'); closed=advance(svc,t,'resolve')
    assert closed.status.value=='resolved' and closed.resolution
    assert svc.list_resources('student','uni-a')[0].service_state=='available'
    assert svc.list_bookings('admin','uni-a')[0].state.value=='cancelled'
    assert book(svc,r,actor='student2').state.value=='confirmed'


def test_dismiss_keeps_reservations(setup_phase16):
    svc=setup_phase16; r=add(svc); b=book(svc,r)
    t=advance(svc,report(svc,r),'dismiss'); assert t.status.value=='dismissed'
    assert svc.list_bookings('admin','uni-a')[0].state.value=='confirmed'
    assert svc.list_resources('admin','uni-a')[0].service_state=='available'


@pytest.mark.parametrize('action', ['start', 'resolve', 'dismiss'])
def test_student_cannot_admin_transition(setup_phase16,action):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(PermissionError,match='administrator'):
        advance(svc,t,action,actor='student')


def test_auditor_readonly_report_blocked(setup_phase16):
    svc=setup_phase16;r=add(svc)
    with pytest.raises(PermissionError,match='read_only'):
        report(svc,r,actor='auditor')
    assert svc.maintenance_tickets('auditor','uni-a')==()


def test_active_membership_required_to_report_and_list(setup_phase16):
    svc=setup_phase16;r=add(svc)
    svc.campus.members.pop(('uni-a','student'))
    with pytest.raises(PermissionError,match='membership'): report(svc,r)
    with pytest.raises(PermissionError,match='membership'):svc.maintenance_tickets('student','uni-a')


def test_cross_tenant_lifecycle_cannot_expose_or_mutate(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(PermissionError,match='membership'):report(svc,r,'student-b','uni-a')
    with pytest.raises(ValueError,match='unavailable'):report(svc,r,'student-b','uni-b')
    with pytest.raises(ValueError,match='not_found'):advance(svc,t,'start',actor='admin-b',institution='uni-b')
    assert svc.maintenance_tickets('admin-b','uni-b')==()
    assert svc.list_resources('student','uni-a')[0].service_state=='available'


def test_non_staff_cannot_see_other_reporters_ticket(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r,'student')
    assert svc.maintenance_tickets('student2','uni-a')==()
    assert [x.id for x in svc.maintenance_tickets('admin','uni-a')] == [t.id]
    assert svc.maintenance_tickets('faculty','uni-a')==()


def test_duplicate_open_ticket_blocked_and_post_resolution_allowed(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(ValueError,match='conflict'):report(svc,r,'student2')
    advance(svc,t,'dismiss')
    assert report(svc,r,'student2').id != t.id


def test_stale_versions_and_illegal_transition_rejected(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(ValueError,match='conflict'):
        svc.transition_maintenance('admin','uni-a',t.id,999,'start')
    t=advance(svc,t,'start')
    with pytest.raises(ValueError,match='conflict'):
        svc.transition_maintenance('admin','uni-a',t.id,1,'resolve','Réparée entièrement.')
    with pytest.raises(ValueError,match='conflict'):
        advance(svc,t,'dismiss')
    with pytest.raises(ValueError,match='conflict'):
        advance(svc,t,'start')


def test_no_deactivation_with_open_maintenance(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(ValueError,match='conflict'):
        svc.deactivate_resource('admin','uni-a',r.id,1)
    advance(svc,t,'dismiss')
    assert not svc.deactivate_resource('admin','uni-a',r.id,2).active


@pytest.mark.parametrize('description', ['', 'a'*7, 'a'*501])
def test_invalid_report_rejected(setup_phase16,description):
    svc=setup_phase16;r=add(svc)
    with pytest.raises(ValueError,match='description'):
        svc.report_maintenance('student','uni-a',r.id,description)


@pytest.mark.parametrize('action, note', [('start','x'*501),('resolve','short'),('dismiss',''),('invalid','some words')])
def test_invalid_transitions_rejected(setup_phase16,action,note):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    with pytest.raises(ValueError,match='invalid'):
        svc.transition_maintenance('admin','uni-a',t.id,1,action,note)


def test_resolve_saves_diagnosis_and_row_version(setup_phase16):
    svc=setup_phase16;r=add(svc);t=advance(svc,report(svc,r),'start')
    t=svc.transition_maintenance('admin','uni-a',t.id,2,'resolve','Changement de composant réalisé.')
    assert t.row_version==3 and t.resolution=='Changement de composant réalisé.'
    assert svc.maintenance_tickets('admin','uni-a')[0].id==t.id


def test_http_paths_authorization_versions_and_visibility(setup_phase16):
    service=setup_phase16;resource=add(service)
    saved=runtime.campus_services;runtime.campus_services=service
    client=TestClient(app)
    def as_user(name):
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id=name)
    base='/v1/campus-services/institutions/uni-a/maintenance'
    try:
        as_user('student')
        r=client.post(base,json={'resource_id':resource.id,'description':'Défaut visible sur le matériel.'})
        assert r.status_code==200,r.text
        ticket=r.json(); assert ticket['status']=='reported'
        assert client.post(base+'/'+ticket['id']+'/start',json={'expected_version':1}).status_code==403
        as_user('admin-b')
        assert client.get(base).status_code==403
        as_user('admin')
        r=client.post(base+'/'+ticket['id']+'/start',json={'expected_version':1})
        assert r.status_code==200,r.text
        assert r.json()['status']=='in_progress'
        assert client.post(base+'/'+ticket['id']+'/start',json={'expected_version':1}).status_code==409
        r=client.post(base+'/'+ticket['id']+'/resolve',json={
            'expected_version':2,'note':'Pièce remplacée et contrôle réalisé.'})
        assert r.status_code==200,r.text
        assert r.json()['status']=='resolved'
        assert len(client.get(base).json())==1
    finally:
        app.dependency_overrides.pop(current_auth,None)
        runtime.campus_services=saved


def test_database_partial_unique_and_cancel_reason_exposed(setup_phase16):
    svc=setup_phase16;r=add(svc);t=report(svc,r)
    other=book(svc,r)
    advance(svc,t,'start')
    assert svc.list_bookings('student','uni-a')[0].cancellation_reason=='resource_maintenance'
    rows=svc.repo.maintenance_tickets('uni-a')
    assert rows[0].status.value == 'in_progress'
