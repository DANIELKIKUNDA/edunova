"""Phase 16: circulation d'ouvrages physiques, RBAC et séparation des tenants."""
from datetime import timedelta
from uuid import uuid4
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState
from app.modules.campus_services.domain.physical_library import PhysicalBook, PhysicalCopy, PhysicalLoan

_ADMINS = frozenset({CampusRole.OWNER, CampusRole.RECTOR, CampusRole.ADMIN, CampusRole.ACADEMIC_ADMIN})
_READ_ALL = _ADMINS | {CampusRole.AUDITOR}
# Fixed v1.0 library circulation policy. Tenant-customisable policies remain future work.
LOAN_DAYS = 21
MAX_OPEN_LOANS = 3
MAX_RENEWALS = 2
RENEWAL_DAYS = 14


class PhysicalLibraryService:
    def __init__(self, repo, campus, now, audit=None):
        self.repo, self.campus, self.now, self.audit = repo, campus, now, audit

    def _member(self, account, institution):
        member = self.campus.membership(institution, account)
        if member is None or member.state != MembershipState.ACTIVE:
            raise PermissionError('campus_library_active_membership_required')
        uni = self.campus.institution(institution)
        if uni is None or uni.state != InstitutionState.ACTIVE:
            raise PermissionError('campus_library_institution_not_active')
        return member

    def _admin(self, account, institution):
        member = self._member(account, institution)
        if member.role not in _ADMINS:
            raise PermissionError('campus_library_admin_required')
        return member

    def _audit(self, account, action, target, identifier):
        if self.audit:
            self.audit.write(actor_account_id=account, action=action,
                             target_type=target, target_id=identifier, metadata={})

    def policy(self, account, institution):
        self._member(account, institution)
        return self.repo.policy(institution)

    def update_policy(self, account, institution, *, expected_version, loan_days,
                      max_open_loans, max_renewals, renewal_days):
        self._admin(account, institution)
        for value, lo, hi in ((loan_days, 1, 60), (max_open_loans, 1, 10),
                               (max_renewals, 0, 2), (renewal_days, 1, 30)):
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError('campus_library_policy_invalid')
        if type(expected_version) is not int or expected_version < 0:
            raise ValueError('campus_library_version_invalid')
        result = self.repo.update_policy(institution, expected_version=expected_version,
            loan_days=loan_days, max_open_loans=max_open_loans,
            max_renewals=max_renewals, renewal_days=renewal_days, now=self.now())
        self._audit(account, 'campus.library.policy.updated', 'campus_library_policy', institution)
        return result

    def add_book(self, account, institution, *, title, author, isbn=''):
        self._admin(account, institution)
        title, author, isbn = title.strip(), author.strip(), isbn.strip()
        if not (1 <= len(title) <= 240 and 1 <= len(author) <= 180 and len(isbn) <= 32):
            raise ValueError('campus_library_book_invalid')
        book = PhysicalBook('libb_' + uuid4().hex, institution, title, author, isbn, self.now())
        self.repo.add_book(book)
        self._audit(account, 'campus.library.book.created', 'campus_library_book', book.id)
        return book

    def books(self, account, institution):
        self._member(account, institution)
        return self.repo.books(institution)

    def add_copy(self, account, institution, *, book_id, barcode):
        self._admin(account, institution)
        barcode = barcode.strip().upper()
        if not 1 <= len(barcode) <= 64:
            raise ValueError('campus_library_barcode_invalid')
        copy = PhysicalCopy('libc_' + uuid4().hex, institution, book_id, barcode, True, self.now())
        self.repo.add_copy(copy)
        self._audit(account, 'campus.library.copy.created', 'campus_library_copy', copy.id)
        return copy

    def copies(self, account, institution, *, book_id=None):
        self._member(account, institution)
        return self.repo.copies(institution, book_id=book_id)

    def available_copy_ids(self, account, institution):
        self._member(account, institution)
        return self.repo.available_copy_ids(institution)

    def borrow(self, account, institution, *, copy_id):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_library_auditor_read_only')
        now = self.now()
        loan = PhysicalLoan('libl_' + uuid4().hex, institution, copy_id, account,
                            now, now + timedelta(days=LOAN_DAYS), None, 1)
        # Borrower caps and overdue-block checks happen in the SAME DB transaction
        # as the loan insertion. The repository serializes borrower changes on PG.
        loan = self.repo.borrow(loan, now)
        self._audit(account, 'campus.library.loan.created', 'campus_library_loan', loan.id)
        return loan

    def loans(self, account, institution):
        member = self._member(account, institution)
        borrower = None if member.role in _READ_ALL else account
        return self.repo.loans(institution, borrower=borrower)

    def eligible_renewal_ids(self, account, institution):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            return frozenset()
        return self.repo.eligible_renewal_ids(institution, account, self.now())

    def renew_loan(self, account, institution, *, loan_id, expected_version):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_library_auditor_read_only')
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_library_version_invalid')
        # Only the actual borrower can prolong their own loan. Repository checks
        # the borrower and the tenant in the same query, before mutating data.
        result = self.repo.renew_loan(institution, loan_id, account,
                                      expected_version, self.now())
        self._audit(account, 'campus.library.loan.renewed', 'campus_library_loan', loan_id)
        return result

    def return_loan(self, account, institution, *, loan_id, expected_version):
        # A borrower cannot self-certify physical restitution.
        # Check-in is an inventory mutation requiring authorised library staff.
        self._admin(account, institution)
        current = self.repo.loan(institution, loan_id)
        if current is None:
            raise ValueError('campus_library_loan_not_found')
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_library_version_invalid')
        result = self.repo.return_loan(institution, loan_id, expected_version, self.now())
        self._audit(account, 'campus.library.loan.returned', 'campus_library_loan', loan_id)
        return result


    def report_loan_incident(self, account, institution, *, loan_id, expected_version, condition):
        """A staff-confirmed loss/damage closes the loan and quarantines its copy."""
        self._admin(account, institution)
        if condition not in ('lost', 'damaged'):
            raise ValueError('campus_library_incident_invalid')
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_library_version_invalid')
        result = self.repo.close_loan_with_incident(
            institution, loan_id, expected_version, condition, self.now())
        self._audit(account, 'campus.library.loan.' + condition,
                    'campus_library_loan', loan_id)
        return result

    def restore_damaged_copy(self, account, institution, *, copy_id, expected_version):
        self._admin(account, institution)
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_library_version_invalid')
        result = self.repo.restore_damaged_copy(institution, copy_id, expected_version)
        self._audit(account, 'campus.library.copy.restored', 'campus_library_copy', copy_id)
        return result
