"""Phase 16 v0.51.3: tenant policy, optimistic concurrency, role and API contracts.

SQLite integration tests; PostgreSQL advisory locking requires Phase 23 certification.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalLibraryPolicyRow
from test_phase16_physical_library_v0_51_1 import library, provision, NOW


def set_policy(service, account='admin', tenant='a', version=0, *, days=14,
               quota=2, renewals=1, extension=7):
    return service.update_policy(account, tenant, expected_version=version,
        loan_days=days, max_open_loans=quota, max_renewals=renewals,
        renewal_days=extension)


def create_copies(service, count=4):
    book, first = provision(service, barcode='POLICY-0')
    return [first] + [service.add_copy('admin', 'a', book_id=book.id,
                                      barcode=f'POLICY-{n}') for n in range(1, count)]


def test_default_policy_is_readable_to_member_without_creating_row(library):
    p = library.policy('alice', 'a')
    assert (p.loan_days, p.max_open_loans, p.max_renewals, p.renewal_days, p.row_version) == (21, 3, 2, 14, 0)
    assert p.updated_at is None
    with library.repo.sf() as session:
        assert session.get(PhysicalLibraryPolicyRow, 'a') is None


def test_policy_customisation_borrow_quota_and_renewal(library):
    p = set_policy(library)
    assert p.row_version == 1 and p.loan_days == 14
    copies = create_copies(library)
    x = library.borrow('alice', 'a', copy_id=copies[0].id)
    y = library.borrow('alice', 'a', copy_id=copies[1].id)
    assert x.due_at == NOW + timedelta(days=14)
    with pytest.raises(ValueError, match='quota'):
        library.borrow('alice', 'a', copy_id=copies[2].id)
    assert library.borrow('bob', 'a', copy_id=copies[2].id)
    extended = library.renew_loan('alice', 'a', loan_id=x.id, expected_version=1)
    assert extended.due_at == x.due_at + timedelta(days=7)
    with pytest.raises(ValueError, match='renewal_limit'):
        library.renew_loan('alice', 'a', loan_id=x.id, expected_version=2)
    assert y.renewal_count == 0


def test_policy_updates_only_affect_future_borrowing_and_renewals(library):
    copies = create_copies(library)
    original = library.borrow('alice', 'a', copy_id=copies[0].id)
    p = set_policy(library, days=9, quota=2, renewals=1, extension=3)
    assert original.due_at == NOW + timedelta(days=21)
    second = library.borrow('alice', 'a', copy_id=copies[1].id)
    assert second.due_at == NOW + timedelta(days=9)
    renewed = library.renew_loan('alice', 'a', loan_id=original.id, expected_version=1)
    assert renewed.due_at == original.due_at + timedelta(days=3)
    after = set_policy(library, version=p.row_version, days=60, quota=10,
                       renewals=2, extension=15)
    assert after.row_version == 2
    renewed2 = library.renew_loan('alice', 'a', loan_id=original.id, expected_version=2)
    assert renewed2.due_at == renewed.due_at + timedelta(days=15)


def test_zero_renewals_and_no_renewal_eligibility(library):
    set_policy(library, renewals=0)
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    assert not library.eligible_renewal_ids('alice', 'a')
    with pytest.raises(ValueError, match='renewal_limit'):
        library.renew_loan('alice', 'a', loan_id=loan.id, expected_version=1)


def test_tenant_separation_policies_and_memberships(library):
    set_policy(library, days=5, quota=1)
    assert library.policy('student-b', 'b').loan_days == 21
    p2 = set_policy(library, 'admin-b', 'b', days=35, quota=8)
    assert p2.row_version == 1
    assert library.policy('alice', 'a').loan_days == 5
    assert library.policy('student-b', 'b').loan_days == 35
    _, copy_b = provision(library, 'b', 'admin-b', 'TENANT-B')
    assert library.borrow('student-b', 'b', copy_id=copy_b.id).due_at == NOW + timedelta(days=35)
    with pytest.raises(PermissionError, match='membership'):
        library.policy('alice', 'b')
    with pytest.raises(PermissionError, match='membership'):
        set_policy(library, 'admin', 'b')


def test_unauthorized_roles_revoked_and_inactive_institution(library):
    for account in ('alice', 'auditor', 'faculty'):
        with pytest.raises(PermissionError, match='admin'):
            set_policy(library, account)
    library.campus.members.pop(('a', 'alice'))
    with pytest.raises(PermissionError, match='membership'):
        library.policy('alice', 'a')
    from types import SimpleNamespace
    from app.modules.campus.domain.model import InstitutionState
    library.campus.institution = lambda i: SimpleNamespace(state=InstitutionState.SUSPENDED)
    with pytest.raises(PermissionError, match='not_active'):
        library.policy('admin', 'a')
    with pytest.raises(PermissionError, match='not_active'):
        set_policy(library)


def test_stale_version_and_replay_are_rejected_unchanged(library):
    initial = set_policy(library)
    before = library.policy('admin', 'a')
    with pytest.raises(ValueError, match='concurrent'):
        set_policy(library, version=0, days=45)
    assert library.policy('admin', 'a') == before
    updated = set_policy(library, version=1, days=18)
    with pytest.raises(ValueError, match='concurrent'):
        set_policy(library, version=1, days=42)
    assert initial.row_version == 1 and updated.row_version == 2
    assert library.policy('admin', 'a').loan_days == 18


@pytest.mark.parametrize('field,value', [('loan_days', 0), ('loan_days', 61),
    ('max_open_loans', 0), ('max_open_loans', 11), ('max_renewals', -1),
    ('max_renewals', 3), ('renewal_days', 0), ('renewal_days', 31),
    ('loan_days', True), ('max_open_loans', 1.5), ('max_renewals', '1')])
def test_bad_policy_fields_rejected_before_write(library, field, value):
    options = {'expected_version': 0, 'loan_days': 21, 'max_open_loans': 3,
               'max_renewals': 2, 'renewal_days': 14}
    options[field] = value
    with pytest.raises(ValueError, match='invalid'):
        library.update_policy('admin', 'a', **options)
    assert library.policy('admin', 'a').row_version == 0


@pytest.mark.parametrize('value', [-1, True, 1.5, '0'])
def test_bad_cas_version_denied(library, value):
    with pytest.raises(ValueError, match='version'):
        set_policy(library, version=value)


def test_db_checks_reject_direct_out_of_range_policy(library):
    with pytest.raises(IntegrityError):
        with library.repo.sf.begin() as session:
            session.add(PhysicalLibraryPolicyRow(institution_id='a',
                loan_days=1000, max_open_loans=3, max_renewals=2,
                renewal_days=14, row_version=1, updated_at=NOW))
    assert library.policy('admin', 'a').row_version == 0


def test_policy_cannot_increase_existing_loan_due_at(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    set_policy(library, days=60)
    persisted = library.repo.loan('a', loan.id)
    assert persisted.due_at == loan.due_at


def test_policy_audit_is_generated_only_after_success(library):
    class Auditor:
        def __init__(self): self.events = []
        def write(self, **kwargs): self.events.append(kwargs)
    auditor = Auditor()
    library.audit = auditor
    p = set_policy(library)
    assert len(auditor.events) == 1
    assert auditor.events[0]['action'] == 'campus.library.policy.updated'
    with pytest.raises(ValueError, match='concurrent'):
        set_policy(library, version=0)
    assert len(auditor.events) == 1
    assert p.row_version == 1


def test_http_policy_read_write_rbac_tenants_cas_and_invalid_input(library):
    old = runtime.physical_library
    runtime.physical_library = library
    client = TestClient(app)
    url = '/v1/campus-services/institutions/a/library/policy'
    data = {'expected_version': 0, 'loan_days': 12, 'max_open_loans': 4,
            'max_renewals': 1, 'renewal_days': 6}
    try:
        app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='alice')
        first = client.get(url)
        assert first.status_code == 200 and first.json()['row_version'] == 0
        assert client.put(url, json=data).status_code == 403
        app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='admin')
        r = client.put(url, json=data)
        assert r.status_code == 200, r.text
        assert r.json()['row_version'] == 1
        assert client.put(url, json=data).status_code == 409
        assert client.get(url).json()['loan_days'] == 12
        assert client.put(url, json={**data, 'expected_version': 1, 'loan_days': 99}).status_code == 422
        assert client.put(url, json={**data, 'expected_version': 1, 'max_renewals': 4}).status_code == 422
        assert client.put(url, json={**data, 'expected_version': -1}).status_code == 422
        assert client.put(url, json={**data, 'expected_version': 1, 'loan_days': 20}).json()['row_version'] == 2
        app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='student-b')
        assert client.get(url).status_code == 403
        assert client.put(url, json=data).status_code == 403
        assert client.get('/v1/campus-services/institutions/b/library/policy').status_code == 200
    finally:
        runtime.physical_library = old
        app.dependency_overrides.pop(current_auth, None)
