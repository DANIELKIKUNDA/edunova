"""Phase 16: on-demand private Campus feed, actual SQL and HTTP adversarial tests."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.main import app
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus_services.application.campus_alerts_service import CampusAlertsService
from app.modules.campus_services.infrastructure.campus_alerts_repo import SqlCampusAlertsRepository
from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalLoanRow
from app.modules.campus_services.infrastructure.event_registration_repo import CampusEventRegistrationRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow
from app.modules.campus_services.application.physical_library_service import PhysicalLibraryService
from app.modules.campus_services.infrastructure.physical_library_repo import SqlPhysicalLibraryRepository
from test_phase16_campus_resources_v0_51_0 import setup_phase16, add, book, NOW


def feed(svc, current=NOW):
    return CampusAlertsService(SqlCampusAlertsRepository(svc.repo.sf), svc, lambda: current)


def checkout(svc, *, borrower='student', university='uni-a', barcode='A-1'):
    lib = PhysicalLibraryService(SqlPhysicalLibraryRepository(svc.repo.sf), svc.campus, lambda: NOW)
    title = lib.add_book('admin' if university == 'uni-a' else 'admin-b', university,
                         title='Physique fondamentale', author='Auteur')
    copy = lib.add_copy('admin' if university == 'uni-a' else 'admin-b', university,
                        book_id=title.id, barcode=barcode)
    return lib, lib.borrow(borrower, university, copy_id=copy.id)


def change_due(svc, loan_id, *, due_days, borrowed_days=-35):
    with svc.repo.sf.begin() as session:
        session.execute(update(PhysicalLoanRow).where(PhysicalLoanRow.id == loan_id).values(
            borrowed_at=NOW+timedelta(days=borrowed_days),
            due_at=NOW+timedelta(days=due_days)))


def add_event(svc, *, university='uni-a', account='student', state='scheduled', starts_hours=12,
              reg_state='registered', mismatch=False):
    import uuid
    rid = 'cev_' + uuid.uuid4().hex
    start = NOW + timedelta(hours=starts_hours)
    with svc.repo.sf.begin() as s:
        s.add(CalendarEventRow(id=rid, institution_id=university, offering_id=None,
            cohort_id=None, kind='event', title='Séminaire', details='Détails',
            starts_at=start, ends_at=start+timedelta(hours=2), location='Campus',
            state=state, source_ref=None, row_version=1, created_by='admin',
            created_at=NOW, updated_at=NOW, registration_capacity=100))
        s.add(CampusEventRegistrationRow(id='evr_'+uuid.uuid4().hex,
            institution_id='uni-b' if mismatch else university,
            event_id=rid, account_id=account, state=reg_state,
            row_version=1, created_at=NOW, updated_at=NOW))
    return rid


def test_due_soon_and_overdue_are_personal_and_deterministic(setup_phase16):
    svc=setup_phase16
    _, first=checkout(svc)
    change_due(svc,first.id,due_days=2)
    alerts=feed(svc).for_account('student','uni-a')
    assert len(alerts)==1 and alerts[0]['kind']=='library_due'
    assert alerts[0]['id']=='library_due:'+first.id
    assert not any('account' in key or 'institution' in key for key in alerts[0])
    change_due(svc,first.id,due_days=-1)
    alert=feed(svc).for_account('student','uni-a')[0]
    assert alert['kind']=='library_overdue' and alert['level']=='urgent'
    assert feed(svc).for_account('student2','uni-a')==[]
    assert feed(svc).for_account('student-b','uni-b')==[]


def test_loan_renewal_and_restitution_clear_alerts(setup_phase16):
    svc=setup_phase16
    lib, loan=checkout(svc)
    change_due(svc, loan.id, due_days=2)
    assert len(feed(svc).for_account('student','uni-a'))==1
    renewed=lib.renew_loan('student','uni-a',loan_id=loan.id,expected_version=1)
    assert renewed.row_version==2
    assert feed(svc).for_account('student','uni-a')==[]
    lib.return_loan('admin','uni-a',loan_id=loan.id,expected_version=2)
    assert feed(svc).for_account('student','uni-a')==[]


def test_maintenance_cancellation_alert_but_voluntary_cancel_not_alert(setup_phase16):
    svc=setup_phase16
    resource=add(svc); own=book(svc,resource)
    ticket=svc.report_maintenance('student','uni-a',resource.id,'Panne électrique nécessitant réparation')
    svc.transition_maintenance('admin','uni-a',ticket.id,1,'start')
    alert=feed(svc).for_account('student','uni-a')
    assert len(alert)==1 and alert[0]['kind']=='booking_maintenance'
    assert feed(svc).for_account('student2','uni-a')==[]
    assert feed(svc).for_account('admin','uni-a')==[]
    # A user cancellation has a different reason and must not trigger a maintenance warning.
    svc.transition_maintenance('admin','uni-a',ticket.id,2,'resolve','Équipement réparé et vérifié')
    separate=book(svc,resource,actor='student2',start=NOW+timedelta(days=2))
    svc.cancel_booking('student2','uni-a',separate.id,1)
    assert feed(svc).for_account('student2','uni-a')==[]


def test_maintenance_cancellation_alert_expires(setup_phase16):
    svc=setup_phase16; resource=add(svc); book(svc,resource)
    ticket=svc.report_maintenance('student','uni-a',resource.id,'Blocage anormal des portes du laboratoire')
    svc.transition_maintenance('admin','uni-a',ticket.id,1,'start')
    assert feed(svc, NOW+timedelta(days=20)).for_account('student','uni-a')==[]


def test_event_soon_and_cancelled_only_active_self_registration(setup_phase16):
    svc=setup_phase16
    identifier=add_event(svc)
    first=feed(svc).for_account('student','uni-a')
    assert first[0]['id']=='event_soon:'+identifier
    assert feed(svc).for_account('admin','uni-a')==[]
    assert feed(svc).for_account('student2','uni-a')==[]
    with svc.repo.sf.begin() as s:
        s.execute(update(CalendarEventRow).where(CalendarEventRow.id==identifier).values(state='cancelled'))
    second=feed(svc).for_account('student','uni-a')
    assert second[0]['kind']=='event_cancelled'
    with svc.repo.sf.begin() as s:
        s.execute(update(CampusEventRegistrationRow).where(
            CampusEventRegistrationRow.event_id==identifier).values(state='cancelled'))
    assert feed(svc).for_account('student','uni-a')==[]


def test_cross_tenant_event_registration_inconsistency_is_never_leaked(setup_phase16):
    svc=setup_phase16
    add_event(svc, university='uni-a', account='student-b', mismatch=True)
    add_event(svc, university='uni-b', account='student', mismatch=False)
    assert feed(svc).for_account('student-b','uni-b')==[]
    assert feed(svc).for_account('student','uni-a')==[]


def test_outside_24h_no_event_reminder_and_cancelled_recent_window(setup_phase16):
    svc=setup_phase16
    add_event(svc,starts_hours=48)
    assert feed(svc).for_account('student','uni-a')==[]
    add_event(svc,state='cancelled',starts_hours=-240)
    assert feed(svc).for_account('student','uni-a')==[]


def test_denied_inactive_membership_and_suspended_university(setup_phase16):
    svc=setup_phase16
    svc.campus.members.pop(('uni-a','student'))
    with pytest.raises(PermissionError,match='membership'):
        feed(svc).for_account('student','uni-a')
    svc.campus.members[('uni-a','student')] = svc.campus.members[('uni-a','student2')]
    svc.campus.institution=lambda i: SimpleNamespace(state='suspended')
    with pytest.raises(PermissionError,match='not_active'):
        feed(svc).for_account('student','uni-a')


def test_admin_may_see_only_personal_alerts_not_all_university(setup_phase16):
    svc=setup_phase16
    _,loan=checkout(svc)
    change_due(svc,loan.id,due_days=-1)
    assert feed(svc).for_account('admin','uni-a')==[]
    assert len(feed(svc).for_account('student','uni-a'))==1
    assert feed(svc).for_account('auditor','uni-a')==[]


def test_no_external_delivery_or_side_effect_on_repeated_get(setup_phase16):
    svc=setup_phase16
    _,loan=checkout(svc)
    change_due(svc,loan.id,due_days=0)
    service=feed(svc)
    assert service.for_account('student','uni-a')==service.for_account('student','uni-a')
    with svc.repo.sf() as s:
        row=s.scalar(select(PhysicalLoanRow).where(PhysicalLoanRow.id==loan.id))
        assert row.returned_at is None and row.row_version==1


def test_limit_and_severity_order_without_full_export():
    class StubRepo:
        def evidence(self, institution, account):
            return ([(f'{x}',NOW+timedelta(days=2)) for x in range(200)],
                    [], [('near', NOW+timedelta(hours=2),NOW+timedelta(hours=3),'scheduled')])
    class Services:
        def _member(self, account, institution): return True
    values=CampusAlertsService(StubRepo(),Services(),lambda: NOW).for_account('a','i')
    assert len(values)==50
    assert values[0]['kind']=='library_due'
    assert all(x['level']=='warning' for x in values)


def test_http_bearer_institution_scope_and_contract(setup_phase16):
    service=feed(setup_phase16)
    previous=runtime.campus_alerts
    runtime.campus_alerts=service
    client=TestClient(app)
    try:
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student')
        response=client.get('/v1/campus-services/institutions/uni-a/alerts')
        assert response.status_code==200 and response.json()==[]
        response=client.get('/v1/campus-services/institutions/uni-b/alerts')
        assert response.status_code==403
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student-b')
        assert client.get('/v1/campus-services/institutions/uni-a/alerts').status_code==403
    finally:
        runtime.campus_alerts=previous
        app.dependency_overrides.pop(current_auth,None)
