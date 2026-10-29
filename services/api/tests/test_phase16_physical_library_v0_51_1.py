"""Physical books and lending: positive paths, adversarial tenant/role/version tests."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.shared.infrastructure.database import Base
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState
from app.modules.campus_services.application.physical_library_service import PhysicalLibraryService
from app.modules.campus_services.infrastructure.physical_library_repo import SqlPhysicalLibraryRepository
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.main import app
from app.runtime import runtime

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)

class Campus:
    def __init__(self):
        self.members = {
            ('a','admin'):CampusRole.ADMIN, ('a','alice'):CampusRole.STUDENT,
            ('a','bob'):CampusRole.STUDENT, ('a','auditor'):CampusRole.AUDITOR,
            ('a','faculty'):CampusRole.FACULTY_ADMIN, ('b','admin-b'):CampusRole.ADMIN,
            ('b','student-b'):CampusRole.STUDENT,
        }
    def membership(self, institution, account):
        role = self.members.get((institution,account))
        return SimpleNamespace(role=role, state=MembershipState.ACTIVE) if role else None
    def institution(self, institution):
        return SimpleNamespace(state=InstitutionState.ACTIVE) if institution in {'a','b'} else None

@pytest.fixture
def library():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    repo = SqlPhysicalLibraryRepository(sessionmaker(bind=engine, expire_on_commit=False))
    service = PhysicalLibraryService(repo, Campus(), lambda: NOW)
    yield service
    engine.dispose()

def provision(service, institution='a', admin='admin', barcode='EX-01'):
    book = service.add_book(admin,institution,title='Physique',author='P. Curie',isbn='9781234567890')
    copy = service.add_copy(admin,institution,book_id=book.id,barcode=barcode)
    return book,copy

def test_catalog_and_borrow_return_reborrow(library):
    book,copy=provision(library)
    assert library.books('alice','a')[0].title=='Physique'
    assert library.copies('alice','a',book_id=book.id)[0].barcode=='EX-01'
    loan=library.borrow('alice','a',copy_id=copy.id)
    assert loan.due_at == NOW+timedelta(days=21)
    assert [x.id for x in library.loans('alice','a')]==[loan.id]
    assert copy.id not in library.available_copy_ids('bob','a')
    with pytest.raises(ValueError,match='unavailable'):
        library.borrow('bob','a',copy_id=copy.id)
    returned=library.return_loan('admin','a',loan_id=loan.id,expected_version=1)
    assert returned.row_version==2 and returned.returned_at==NOW
    again=library.borrow('bob','a',copy_id=copy.id)
    assert again.id!=loan.id
    assert copy.id not in library.available_copy_ids('alice','a')

def test_cross_tenant_forged_copy_book_and_loan_blocked(library):
    book,copy=provision(library)
    assert library.books('student-b','b')==()
    with pytest.raises(ValueError,match='not_found'):
        library.add_copy('admin-b','b',book_id=book.id,barcode='EX-02')
    with pytest.raises(ValueError,match='unavailable'):
        library.borrow('student-b','b',copy_id=copy.id)
    loan=library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(ValueError,match='not_found'):
        library.return_loan('admin-b','b',loan_id=loan.id,expected_version=1)
    with pytest.raises(PermissionError,match='membership'):
        library.books('student-b','a')

def test_role_controls_auditor_readonly_faculty_self_only(library):
    book,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    assert library.loans('auditor','a')[0].id==loan.id
    assert library.loans('faculty','a')==()
    assert library.loans('bob','a')==()
    with pytest.raises(PermissionError,match='admin'):
        library.add_book('alice','a',title='Histoire',author='Auteur')
    with pytest.raises(PermissionError,match='admin'):
        library.add_copy('faculty','a',book_id=book.id,barcode='B2')
    with pytest.raises(PermissionError,match='read_only'):
        library.borrow('auditor','a',copy_id=copy.id)
    with pytest.raises(PermissionError,match='admin'):
        library.return_loan('auditor','a',loan_id=loan.id,expected_version=1)
    with pytest.raises(PermissionError,match='admin'):
        library.return_loan('bob','a',loan_id=loan.id,expected_version=1)
    with pytest.raises(PermissionError,match='admin'):
        library.return_loan('alice','a',loan_id=loan.id,expected_version=1)
    assert library.return_loan('admin','a',loan_id=loan.id,expected_version=1).returned_at==NOW

def test_duplicate_barcodes_per_tenant_only(library):
    book,_=provision(library)
    with pytest.raises(ValueError,match='already_exists'):
        library.add_copy('admin','a',book_id=book.id,barcode='ex-01')
    _,other=provision(library,'b','admin-b','EX-01')
    assert other.barcode=='EX-01'

def test_version_cas_prevents_double_return(library):
    _,copy=provision(library)
    loan=library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(ValueError,match='concurrent'):
        library.return_loan('admin','a',loan_id=loan.id,expected_version=2)
    library.return_loan('admin','a',loan_id=loan.id,expected_version=1)
    with pytest.raises(ValueError,match='concurrent'):
        library.return_loan('admin','a',loan_id=loan.id,expected_version=1)

def test_membership_revoked_suspended_institution(library):
    _,copy=provision(library)
    library.campus.members.pop(('a','alice'))
    with pytest.raises(PermissionError,match='membership'):
        library.borrow('alice','a',copy_id=copy.id)
    library.campus.institution=lambda i:SimpleNamespace(state=InstitutionState.SUSPENDED)
    with pytest.raises(PermissionError,match='not_active'):
        library.books('admin','a')

def test_adversarial_blank_inputs_and_duplicate_copy_loan(library):
    with pytest.raises(ValueError,match='invalid'):
        library.add_book('admin','a',title='   ',author='X')
    book,copy=provision(library)
    with pytest.raises(ValueError,match='invalid'):
        library.add_copy('admin','a',book_id=book.id,barcode=' ')
    library.borrow('alice','a',copy_id=copy.id)
    with pytest.raises(ValueError,match='unavailable'):
        library.borrow('alice','a',copy_id=copy.id)

def test_db_unique_open_loan_guards_bypassing_service(library):
    _,copy=provision(library)
    lib=library.borrow('alice','a',copy_id=copy.id)
    from sqlalchemy.exc import IntegrityError
    from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalLoanRow
    with pytest.raises(IntegrityError):
        with library.repo.sf.begin() as session:
            session.add(PhysicalLoanRow(id='forged_2',institution_id='a',copy_id=copy.id,
                borrower_account_id='bob',borrowed_at=NOW,due_at=NOW+timedelta(days=1),
                returned_at=None,row_version=1))
    assert len(library.loans('admin','a'))==1

def test_http_contract_and_authenticated_owner_identity(library):
    before=runtime.physical_library
    runtime.physical_library=library
    app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='admin')
    try:
        client=TestClient(app)
        created=client.post('/v1/campus-services/institutions/a/library/books',json={
            'title':'Algèbre','author':'Professeur','isbn':''})
        assert created.status_code==200,created.text
        book_id=created.json()['id']
        copied=client.post('/v1/campus-services/institutions/a/library/copies',json={
            'book_id':book_id,'barcode':'ALG-01'})
        assert copied.status_code==200,copied.text
        copy_id=copied.json()['id']
        assert client.get('/v1/campus-services/institutions/a/library/copies').json()[0]['available'] is True
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='alice')
        loan=client.post('/v1/campus-services/institutions/a/library/loans',json={
            'copy_id':copy_id,'borrower_account_id':'bob'})
        # Any client-provided actor is ignored by the strict schema; account is token-bound.
        assert loan.status_code==200 and loan.json()['borrower_account_id']=='alice',loan.text
        assert client.post('/v1/campus-services/institutions/a/library/loans',json={
            'copy_id':copy_id}).status_code==409
        assert client.get('/v1/campus-services/institutions/a/library/copies').json()[0]['available'] is False
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='bob')
        assert client.get('/v1/campus-services/institutions/a/library/loans').json()==[]
        assert client.post('/v1/campus-services/institutions/a/library/loans/'+loan.json()['id']+'/return',
            json={'expected_version':1}).status_code==403
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='alice')
        assert client.post('/v1/campus-services/institutions/a/library/loans/'+loan.json()['id']+'/return',
            json={'expected_version':1}).status_code==403
        app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='admin')
        assert client.post('/v1/campus-services/institutions/a/library/loans/'+loan.json()['id']+'/return',
            json={'expected_version':1}).status_code==200
        assert len(client.get('/v1/campus-services/institutions/a/library/books').json())==1
    finally:
        runtime.physical_library=before
        app.dependency_overrides.pop(current_auth,None)
