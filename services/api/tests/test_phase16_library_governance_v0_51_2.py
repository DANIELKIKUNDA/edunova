"""Phase 16 v0.51.2: positive and adversarial physical loan governance tests.

Runs on SQLite to verify application invariants. PostgreSQL advisory locking
and the versioned SQL migration require separate PostgreSQL certification.
"""
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalLoanRow
from test_phase16_physical_library_v0_51_1 import library, provision, NOW


def more_copies(s, count):
    book, first = provision(s, barcode='FIRST')
    return [first] + [s.add_copy('admin', 'a', book_id=book.id, barcode=f'EX-{n}')
                      for n in range(1, count)]


def test_three_open_allowed_fourth_denied_and_return_frees_slot(library):
    copies = more_copies(library, 4)
    loans = [library.borrow('alice', 'a', copy_id=c.id) for c in copies[:3]]
    with pytest.raises(ValueError, match='quota'):
        library.borrow('alice', 'a', copy_id=copies[3].id)
    assert copies[3].id in library.available_copy_ids('bob', 'a')
    library.return_loan('admin', 'a', loan_id=loans[0].id, expected_version=1)
    assert library.borrow('alice', 'a', copy_id=copies[3].id).borrower_account_id == 'alice'


def test_quota_is_isolated_per_borrower_and_institution(library):
    copies = more_copies(library, 5)
    for c in copies[:3]:
        library.borrow('alice', 'a', copy_id=c.id)
    assert library.borrow('bob', 'a', copy_id=copies[3].id).borrower_account_id == 'bob'
    book_b, copy_b = provision(library, 'b', 'admin-b', 'BOOK-B')
    assert library.borrow('student-b', 'b', copy_id=copy_b.id).institution_id == 'b'


def test_overdue_blocks_new_borrow_even_below_quota(library):
    copies = more_copies(library, 2)
    loan = library.borrow('alice', 'a', copy_id=copies[0].id)
    library.now = lambda: NOW + timedelta(days=22)
    with pytest.raises(ValueError, match='overdue'):
        library.borrow('alice', 'a', copy_id=copies[1].id)
    # Other borrowers aren't punished for Alice's late books.
    assert library.borrow('bob', 'a', copy_id=copies[1].id).borrower_account_id == 'bob'
    assert library.return_loan('admin', 'a', loan_id=loan.id, expected_version=1).returned_at is not None


def test_returning_overdue_restores_borrowing_eligibility(library):
    copies = more_copies(library, 2)
    old = library.borrow('alice', 'a', copy_id=copies[0].id)
    library.now = lambda: NOW + timedelta(days=22)
    library.return_loan('admin','a',loan_id=old.id,expected_version=1)
    assert library.borrow('alice','a',copy_id=copies[1].id)


def test_renew_twice_cas_and_retains_identity(library):
    _, copy = provision(library)
    loan = library.borrow('alice', 'a', copy_id=copy.id)
    r1 = library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)
    assert r1.id == loan.id and r1.due_at == loan.due_at + timedelta(days=14)
    assert r1.row_version == 2 and r1.renewal_count == 1 and r1.last_renewed_at == NOW
    r2 = library.renew_loan('alice','a',loan_id=loan.id,expected_version=2)
    assert r2.due_at == loan.due_at + timedelta(days=28)
    assert r2.row_version == 3 and r2.renewal_count == 2
    with pytest.raises(ValueError,match='renewal_limit'):
        library.renew_loan('alice','a',loan_id=loan.id,expected_version=3)
    assert library.repo.loan('a',loan.id).row_version == 3


def test_stale_renewal_does_not_mutate_and_cannot_be_replayed(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    first=library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)
    with pytest.raises(ValueError,match='concurrent'):
        library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)
    assert library.repo.loan('a',loan.id) == first


def test_renewal_rejected_when_self_overdue(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    library.now=lambda: NOW+timedelta(days=21)
    with pytest.raises(ValueError,match='overdue'):
        library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)
    assert library.repo.loan('a',loan.id).renewal_count == 0


def test_renewal_rejected_if_other_active_loan_overdue(library):
    copies=more_copies(library,2)
    older=library.borrow('alice','a',copy_id=copies[0].id)
    library.now=lambda: NOW+timedelta(days=10)
    newer=library.borrow('alice','a',copy_id=copies[1].id)
    library.now=lambda: NOW+timedelta(days=22)
    assert newer.due_at > library.now()
    with pytest.raises(ValueError,match='overdue'):
        library.renew_loan('alice','a',loan_id=newer.id,expected_version=1)
    assert library.repo.loan('a',newer.id).renewal_count == 0


def test_borrower_alone_can_renew_and_tenant_mismatch_hides_loan(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    for account,institution in [('bob','a'),('admin','a'),('student-b','b')]:
        with pytest.raises(ValueError,match='not_found'):
            library.renew_loan(account,institution,loan_id=loan.id,expected_version=1)
    assert library.repo.loan('a',loan.id).row_version == 1


def test_auditor_forbidden_to_renew_even_when_loan_id_known(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(PermissionError,match='read_only'):
        library.renew_loan('auditor','a',loan_id=loan.id,expected_version=1)


def test_revoked_member_cannot_renew(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    library.campus.members.pop(('a','alice'))
    with pytest.raises(PermissionError,match='membership'):
        library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)


def test_return_after_renewal_requires_latest_version(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    new=library.renew_loan('alice','a',loan_id=loan.id,expected_version=1)
    with pytest.raises(ValueError,match='concurrent'):
        library.return_loan('admin','a',loan_id=loan.id,expected_version=1)
    returned=library.return_loan('admin','a',loan_id=loan.id,expected_version=2)
    assert returned.renewal_count == 1 and returned.row_version == 3
    with pytest.raises(ValueError,match='concurrent'):
        library.renew_loan('alice','a',loan_id=loan.id,expected_version=3)


def test_invalid_cas_versions_fail_without_mutation(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    for version in [0,-1,True,'1']:
        with pytest.raises(ValueError,match='version'):
            library.renew_loan('alice','a',loan_id=loan.id,expected_version=version)
    assert library.repo.loan('a',loan.id).row_version == 1


def test_database_rejects_renewal_count_out_of_range(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(IntegrityError):
        with library.repo.sf.begin() as session:
            row=session.get(PhysicalLoanRow,loan.id)
            row.renewal_count=99
    assert library.repo.loan('a',loan.id).renewal_count == 0


def test_http_borrow_quota_and_renewal_contract(library):
    previous=runtime.physical_library
    runtime.physical_library=library
    app.dependency_overrides[current_auth]=lambda: AuthContext(account_id='admin')
    client=TestClient(app)
    try:
        ids=[c.id for c in more_copies(library,4)]
        app.dependency_overrides[current_auth]=lambda: AuthContext(account_id='alice')
        loans=[client.post('/v1/campus-services/institutions/a/library/loans',json={'copy_id':i})
               for i in ids[:3]]
        assert all(x.status_code == 200 for x in loans)
        assert client.post('/v1/campus-services/institutions/a/library/loans',json={'copy_id':ids[3]}).status_code==409
        lid=loans[0].json()['id']
        response=client.post(f'/v1/campus-services/institutions/a/library/loans/{lid}/renew',
                             json={'expected_version':1, 'borrower_account_id':'bob'})
        assert response.status_code==200, response.text
        assert response.json()['borrower_account_id']=='alice'
        assert response.json()['renewal_count']==1
        got=client.get('/v1/campus-services/institutions/a/library/loans')
        assert got.status_code==200 and any(x['can_renew'] is True for x in got.json())
        assert client.post(f'/v1/campus-services/institutions/a/library/loans/{lid}/renew',
                            json={'expected_version':1}).status_code==409
        app.dependency_overrides[current_auth]=lambda: AuthContext(account_id='bob')
        assert client.post(f'/v1/campus-services/institutions/a/library/loans/{lid}/renew',
                           json={'expected_version':2}).status_code==400
    finally:
        runtime.physical_library=previous
        app.dependency_overrides.pop(current_auth,None)


def test_http_returns_422_for_invalid_input_and_denies_tenant(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    previous=runtime.physical_library
    runtime.physical_library=library
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='alice')
    try:
        client=TestClient(app)
        base=f'/v1/campus-services/institutions/a/library/loans/{loan.id}/renew'
        assert client.post(base,json={'expected_version':0}).status_code==422
        assert client.post(base,json={'expected_version':'bad'}).status_code==422
        assert client.post(base,json={'expected_version':1}).status_code==200
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student-b')
        assert client.post(base,json={'expected_version':2}).status_code==403
    finally:
        runtime.physical_library=previous
        app.dependency_overrides.pop(current_auth,None)


def test_get_loan_status_flags_use_full_active_set_not_page_slice(library):
    copies=more_copies(library,2)
    older=library.borrow('alice','a',copy_id=copies[0].id)
    library.now=lambda: NOW+timedelta(days=10)
    newer=library.borrow('alice','a',copy_id=copies[1].id)
    library.now=lambda: NOW+timedelta(days=22)
    prev=runtime.physical_library
    runtime.physical_library=library
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='alice')
    try:
        response=TestClient(app).get('/v1/campus-services/institutions/a/library/loans')
        assert response.status_code==200
        status={row['id']: row for row in response.json()}
        assert status[older.id]['overdue'] is True
        assert status[newer.id]['overdue'] is False
        assert not status[newer.id]['can_renew']  # other volume overdue
    finally:
        runtime.physical_library=prev
        app.dependency_overrides.pop(current_auth,None)


def test_admin_can_return_but_not_renew_a_student_volume(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    prev=runtime.physical_library
    runtime.physical_library=library
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='admin')
    try:
        client=TestClient(app)
        read=client.get('/v1/campus-services/institutions/a/library/loans')
        assert read.status_code==200 and read.json()[0]['can_renew'] is False
        assert client.post(f'/v1/campus-services/institutions/a/library/loans/{loan.id}/renew',
                           json={'expected_version':1}).status_code==400
        assert client.post(f'/v1/campus-services/institutions/a/library/loans/{loan.id}/return',
                           json={'expected_version':1}).status_code==200
    finally:
        runtime.physical_library=prev
        app.dependency_overrides.pop(current_auth,None)
