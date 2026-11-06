"""v0.51.4: loss, damage, restoration, concurrency, RBAC and multi-tenant.

SQLite integration. PostgreSQL row lock / migration certification remains external.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalCopyRow, PhysicalLoanRow
from test_phase16_physical_library_v0_51_1 import library, provision


def test_normal_return_preserves_serviceable_copy_and_reason(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    returned = library.return_loan('admin', 'a', loan_id=loan.id, expected_version=1)
    assert returned.closure_reason == 'returned'
    assert library.copies('alice', 'a')[0].condition == 'serviceable'
    assert copy.id in library.available_copy_ids('bob', 'a')


@pytest.mark.parametrize('condition', ['lost', 'damaged'])
def test_incident_atomic_closure_and_quarantine(library, condition):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    resolved = library.report_loan_incident('admin', 'a', loan_id=loan.id,
                                            expected_version=1, condition=condition)
    current = library.copies('admin', 'a')[0]
    assert resolved.closure_reason == condition and resolved.row_version == 2
    assert resolved.returned_at is not None
    assert not current.active and current.condition == condition and current.row_version == 2
    assert copy.id not in library.available_copy_ids('alice', 'a')
    with pytest.raises(ValueError, match='unavailable'):
        library.borrow('bob', 'a', copy_id=copy.id)
    # History remains visible, no duplicate open loan and no silent resurrection.
    assert library.loans('alice','a')[0].closure_reason == condition


def test_restoring_repaired_damaged_copy_is_cas_and_reborrowable(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    library.report_loan_incident('admin', 'a', loan_id=loan.id, expected_version=1,
                                 condition='damaged')
    fixed = library.restore_damaged_copy('admin', 'a', copy_id=copy.id, expected_version=2)
    assert fixed.condition == 'serviceable' and fixed.active and fixed.row_version == 3
    assert library.borrow('bob', 'a', copy_id=copy.id).borrower_account_id == 'bob'
    with pytest.raises(ValueError, match='concurrent'):
        library.restore_damaged_copy('admin', 'a', copy_id=copy.id, expected_version=2)


def test_lost_copy_cannot_be_reactivated_as_repaired(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    library.report_loan_incident('admin', 'a', loan_id=loan.id, expected_version=1,
                                 condition='lost')
    with pytest.raises(ValueError, match='not_restorable'):
        library.restore_damaged_copy('admin', 'a', copy_id=copy.id, expected_version=2)


def test_replay_return_and_incident_are_rejected(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    library.report_loan_incident('admin', 'a', loan_id=loan.id, expected_version=1,
                                 condition='damaged')
    for operation in [
        lambda: library.report_loan_incident('admin', 'a', loan_id=loan.id,
                                             expected_version=1, condition='lost'),
        lambda: library.return_loan('admin', 'a', loan_id=loan.id, expected_version=1),
        lambda: library.report_loan_incident('admin', 'a', loan_id=loan.id,
                                             expected_version=2, condition='damaged'),
    ]:
        with pytest.raises(ValueError, match='concurrent'):
            operation()
    assert library.repo.loan('a', loan.id).closure_reason == 'damaged'


@pytest.mark.parametrize('account,tenant', [('alice','a'),('auditor','a'),('faculty','a'),
                                             ('admin-b','b')])
def test_non_staff_and_foreign_tenant_cannot_report(library, account, tenant):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    if tenant == 'b':
        with pytest.raises(ValueError, match='not_found'):
            library.report_loan_incident(account, tenant, loan_id=loan.id,
                                         expected_version=1, condition='damaged')
    else:
        with pytest.raises(PermissionError, match='admin'):
            library.report_loan_incident(account, tenant, loan_id=loan.id,
                                         expected_version=1, condition='damaged')
    assert library.repo.loan('a', loan.id).returned_at is None


def test_unprivileged_and_foreign_restoration_denied(library):
    _, copy = provision(library)
    loan = library.borrow('alice','a',copy_id=copy.id)
    library.report_loan_incident('admin','a',loan_id=loan.id,expected_version=1,condition='damaged')
    for account in ('alice', 'auditor'):
        with pytest.raises(PermissionError, match='admin'):
            library.restore_damaged_copy(account,'a',copy_id=copy.id,expected_version=2)
    with pytest.raises(ValueError, match='concurrent'):
        library.restore_damaged_copy('admin-b','b',copy_id=copy.id,expected_version=2)


@pytest.mark.parametrize('condition', ['', 'stolen', 'returned', 'serviceable', None])
def test_incident_condition_whitelist_rejects_invalid(library, condition):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    with pytest.raises(ValueError, match='invalid'):
        library.report_loan_incident('admin', 'a', loan_id=loan.id,
                                     expected_version=1, condition=condition)
    assert library.repo.loan('a', loan.id).returned_at is None


@pytest.mark.parametrize('version', [0, -1, True, '1'])
def test_incident_cas_validates_types(library, version):
    _,copy = provision(library)
    loan = library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(ValueError, match='version'):
        library.report_loan_incident('admin','a',loan_id=loan.id,
                                     expected_version=version,condition='lost')


def test_database_guards_copy_and_loan_resolution(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    with pytest.raises(IntegrityError):
        with library.repo.sf.begin() as session:
            row = session.get(PhysicalCopyRow, copy.id)
            row.condition = 'lost'  # cannot remain active
    with pytest.raises(IntegrityError):
        with library.repo.sf.begin() as session:
            row = session.get(PhysicalLoanRow, loan.id)
            row.closure_reason = 'lost'  # cannot close without returned_at
    assert library.copies('alice','a')[0].active
    assert library.repo.loan('a',loan.id).closure_reason is None


def test_http_contract_and_error_mapping(library):
    previous = runtime.physical_library
    runtime.physical_library = library
    app.dependency_overrides[current_auth] = lambda: AuthContext(account_id='admin')
    try:
        _, copy = provision(library)
        loan = library.borrow('alice','a',copy_id=copy.id)
        client = TestClient(app)
        prefix = '/v1/campus-services/institutions/a/library'
        result = client.post(f'{prefix}/loans/{loan.id}/incident',
                             json={'expected_version':1,'condition':'damaged'})
        assert result.status_code == 200, result.text
        assert result.json()['closure_reason'] == 'damaged'
        assert client.post(f'{prefix}/loans/{loan.id}/incident',
            json={'expected_version':1,'condition':'lost'}).status_code == 409
        assert client.post(f'{prefix}/loans/{loan.id}/incident',
            json={'expected_version':2,'condition':'bad'}).status_code == 422
        result = client.post(f'{prefix}/copies/{copy.id}/restore',
                             json={'expected_version':2})
        assert result.status_code == 200, result.text
        assert result.json()['row_version'] == 3
    finally:
        app.dependency_overrides.pop(current_auth, None)
        runtime.physical_library = previous
