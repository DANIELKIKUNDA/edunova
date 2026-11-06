"""Tenant-scoped physical library repository.

Lock each physical copy before checking circulation; the partial unique active-loan
index is the final database invariant, including across concurrent writers.
PostgreSQL locking must be validated separately on production-class infrastructure.
"""
from datetime import UTC, timedelta
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.campus_services.domain.physical_library import PhysicalBook, PhysicalCopy, PhysicalLoan, PhysicalLibraryPolicy


def _aware(dt):
    return dt if dt is None or dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class PhysicalBookRow(Base):
    __tablename__ = 'campus_library_books'
    __table_args__ = (UniqueConstraint('institution_id', 'id', name='uq_campus_library_books_tenant_id'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    author: Mapped[str] = mapped_column(String(180), nullable=False)
    isbn: Mapped[str] = mapped_column(String(32), nullable=False, default='')
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class PhysicalCopyRow(Base):
    __tablename__ = 'campus_library_copies'
    __table_args__ = (
        UniqueConstraint('institution_id', 'id', name='uq_campus_library_copies_tenant_id'),
        UniqueConstraint('institution_id', 'barcode', name='uq_campus_library_copy_barcode'),
        CheckConstraint("condition IN ('serviceable','damaged','lost','withdrawn')", name='ck_campus_library_copy_condition'),
        CheckConstraint("(condition = 'serviceable' AND active = TRUE) OR (condition <> 'serviceable' AND active = FALSE)", name='ck_campus_library_copy_condition_active'),
        CheckConstraint('row_version >= 1', name='ck_campus_library_copy_version'),
        ForeignKeyConstraint(['institution_id', 'book_id'],
                             ['campus_library_books.institution_id', 'campus_library_books.id']),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    book_id: Mapped[str] = mapped_column(String(64), nullable=False)
    barcode: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    condition: Mapped[str] = mapped_column(String(16), nullable=False, default='serviceable')
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class PhysicalLoanRow(Base):
    __tablename__ = 'campus_library_loans'
    __table_args__ = (
        ForeignKeyConstraint(['institution_id', 'copy_id'],
                             ['campus_library_copies.institution_id', 'campus_library_copies.id']),
        CheckConstraint('due_at > borrowed_at', name='ck_campus_library_due_after_borrow'),
        CheckConstraint('returned_at IS NULL OR returned_at >= borrowed_at',
                        name='ck_campus_library_return_after_borrow'),
        CheckConstraint('row_version >= 1', name='ck_campus_library_loan_version'),
        CheckConstraint('renewal_count >= 0 AND renewal_count <= 2', name='ck_campus_library_loan_renewals'),
        CheckConstraint("(returned_at IS NULL AND closure_reason IS NULL) OR (returned_at IS NOT NULL AND closure_reason IN ('returned','damaged','lost'))", name='ck_campus_library_loan_resolution'),
        Index('uq_campus_library_one_open_loan', 'institution_id', 'copy_id', unique=True,
              postgresql_where=text('returned_at IS NULL'), sqlite_where=text('returned_at IS NULL')),
        Index('ix_campus_library_borrower', 'institution_id', 'borrower_account_id', 'borrowed_at'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    copy_id: Mapped[str] = mapped_column(String(64), nullable=False)
    borrower_account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    borrowed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_renewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)


class PhysicalLibraryPolicyRow(Base):
    __tablename__ = 'campus_library_policies'
    __table_args__ = (
        CheckConstraint('loan_days BETWEEN 1 AND 60', name='ck_campus_lib_policy_loan_days'),
        CheckConstraint('max_open_loans BETWEEN 1 AND 10', name='ck_campus_lib_policy_open'),
        CheckConstraint('max_renewals BETWEEN 0 AND 2', name='ck_campus_lib_policy_renewals'),
        CheckConstraint('renewal_days BETWEEN 1 AND 30', name='ck_campus_lib_policy_renewal_days'),
        CheckConstraint('row_version >= 1', name='ck_campus_lib_policy_version'),
    )
    institution_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    loan_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_open_loans: Mapped[int] = mapped_column(Integer, nullable=False)
    max_renewals: Mapped[int] = mapped_column(Integer, nullable=False)
    renewal_days: Mapped[int] = mapped_column(Integer, nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class SqlPhysicalLibraryRepository:
    def __init__(self, session_factory):
        self.sf = session_factory

    @staticmethod
    def _book(r):
        return PhysicalBook(r.id, r.institution_id, r.title, r.author, r.isbn, _aware(r.created_at))

    @staticmethod
    def _copy(r):
        return PhysicalCopy(r.id, r.institution_id, r.book_id, r.barcode, r.active, _aware(r.created_at), r.condition, r.row_version)

    @staticmethod
    def _loan(r):
        return PhysicalLoan(r.id, r.institution_id, r.copy_id, r.borrower_account_id,
                            _aware(r.borrowed_at), _aware(r.due_at), _aware(r.returned_at),
                            r.row_version, r.renewal_count, _aware(r.last_renewed_at), r.closure_reason)

    @staticmethod
    def _policy(session, institution):
        row = session.get(PhysicalLibraryPolicyRow, institution)
        if row is None:
            return PhysicalLibraryPolicy(institution)
        return PhysicalLibraryPolicy(row.institution_id, row.loan_days, row.max_open_loans,
                                     row.max_renewals, row.renewal_days, row.row_version,
                                     _aware(row.updated_at))

    def policy(self, institution):
        with self.sf() as session:
            return self._policy(session, institution)

    @staticmethod
    def _lock_policy(session, institution):
        # Serialise policy changes with checkouts/renewals within one tenant.
        # PG advisory locks are transaction-scoped; SQLite tests are sequential.
        if session.bind.dialect.name == 'postgresql':
            session.execute(text('SELECT pg_advisory_xact_lock(hashtext(:scope)::bigint)'),
                            {'scope': f'campus_library_policy:{institution}'})

    def update_policy(self, institution, *, expected_version, loan_days,
                      max_open_loans, max_renewals, renewal_days, now):
        # If two writers initialise the absent row concurrently on SQLite,
        # translate the uniqueness failure into a controlled optimistic CAS
        # conflict, rather than exposing an internal database error.
        try:
            return self._update_policy(institution, expected_version=expected_version,
                loan_days=loan_days, max_open_loans=max_open_loans,
                max_renewals=max_renewals, renewal_days=renewal_days, now=now)
        except IntegrityError:
            raise ValueError('campus_library_policy_concurrent_modification') from None

    def _update_policy(self, institution, *, expected_version, loan_days,
                       max_open_loans, max_renewals, renewal_days, now):
        with self.sf.begin() as session:
            self._lock_policy(session, institution)
            row = session.get(PhysicalLibraryPolicyRow, institution, with_for_update=True)
            if row is None:
                if expected_version != 0:
                    raise ValueError('campus_library_policy_concurrent_modification')
                row = PhysicalLibraryPolicyRow(institution_id=institution, loan_days=loan_days,
                    max_open_loans=max_open_loans, max_renewals=max_renewals,
                    renewal_days=renewal_days, row_version=1, updated_at=now)
                session.add(row)
            else:
                if row.row_version != expected_version:
                    raise ValueError('campus_library_policy_concurrent_modification')
                row.loan_days, row.max_open_loans = loan_days, max_open_loans
                row.max_renewals, row.renewal_days = max_renewals, renewal_days
                row.row_version += 1
                row.updated_at = now
            session.flush()
            return self._policy(session, institution)

    def add_book(self, book):
        with self.sf.begin() as session:
            session.add(PhysicalBookRow(**{k: getattr(book, k) for k in book.__dataclass_fields__}))

    def books(self, institution):
        with self.sf() as session:
            return tuple(self._book(r) for r in session.scalars(select(PhysicalBookRow).where(
                PhysicalBookRow.institution_id == institution).order_by(PhysicalBookRow.title).limit(250)).all())

    def add_copy(self, copy):
        try:
            with self.sf.begin() as session:
                book = session.scalar(select(PhysicalBookRow.id).where(
                    PhysicalBookRow.institution_id == copy.institution_id,
                    PhysicalBookRow.id == copy.book_id))
                if book is None:
                    raise ValueError('campus_library_book_not_found')
                session.add(PhysicalCopyRow(**{k: getattr(copy, k) for k in copy.__dataclass_fields__}))
        except IntegrityError:
            raise ValueError('campus_library_barcode_already_exists') from None

    def copies(self, institution, book_id=None):
        with self.sf() as session:
            stmt = select(PhysicalCopyRow).where(PhysicalCopyRow.institution_id == institution)
            if book_id is not None:
                stmt = stmt.where(PhysicalCopyRow.book_id == book_id)
            return tuple(self._copy(r) for r in session.scalars(stmt.order_by(PhysicalCopyRow.barcode).limit(250)).all())

    def available_copy_ids(self, institution):
        with self.sf() as session:
            busy = select(PhysicalLoanRow.copy_id).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.returned_at.is_(None))
            rows = session.scalars(select(PhysicalCopyRow.id).where(
                PhysicalCopyRow.institution_id == institution,
                PhysicalCopyRow.active.is_(True),
                PhysicalCopyRow.id.not_in(busy))).all()
            return frozenset(rows)

    @staticmethod
    def _lock_borrower(session, institution, account):
        # PostgreSQL: transaction-scoped advisory lock by tenant+borrower.
        # Same person borrowing DIFFERENT copies concurrently must be serialized
        # before checking their quota. SQLite tests only sequential semantics.
        if session.bind.dialect.name == 'postgresql':
            session.execute(text('SELECT pg_advisory_xact_lock(hashtext(:scope)::bigint)'),
                            {'scope': f'campus_library:{institution}:{account}'})

    def borrow(self, loan, now):
        try:
            with self.sf.begin() as session:
                self._lock_borrower(session, loan.institution_id, loan.borrower_account_id)
                self._lock_policy(session, loan.institution_id)
                policy = self._policy(session, loan.institution_id)
                active = select(PhysicalLoanRow).where(
                    PhysicalLoanRow.institution_id == loan.institution_id,
                    PhysicalLoanRow.borrower_account_id == loan.borrower_account_id,
                    PhysicalLoanRow.returned_at.is_(None))
                if session.scalar(select(func.count()).select_from(active.subquery())) >= policy.max_open_loans:
                    raise ValueError('campus_library_borrower_quota_exceeded')
                if session.scalar(select(PhysicalLoanRow.id).where(
                    PhysicalLoanRow.institution_id == loan.institution_id,
                    PhysicalLoanRow.borrower_account_id == loan.borrower_account_id,
                    PhysicalLoanRow.returned_at.is_(None),
                    PhysicalLoanRow.due_at <= now).limit(1)) is not None:
                    raise ValueError('campus_library_overdue_loans_block_borrow')
                copy = session.scalar(select(PhysicalCopyRow).where(
                    PhysicalCopyRow.institution_id == loan.institution_id,
                    PhysicalCopyRow.id == loan.copy_id).with_for_update())
                if copy is None or not copy.active or copy.condition != 'serviceable':
                    raise ValueError('campus_library_copy_unavailable')
                held = session.scalar(select(PhysicalLoanRow.id).where(
                    PhysicalLoanRow.institution_id == loan.institution_id,
                    PhysicalLoanRow.copy_id == loan.copy_id,
                    PhysicalLoanRow.returned_at.is_(None)).limit(1))
                if held is not None:
                    raise ValueError('campus_library_copy_unavailable')
                data = {k: getattr(loan, k) for k in loan.__dataclass_fields__}
                data['due_at'] = now + timedelta(days=policy.loan_days)
                row = PhysicalLoanRow(**data)
                session.add(row)
                session.flush()
                return self._loan(row)
        except IntegrityError:
            raise ValueError('campus_library_copy_unavailable') from None

    def loan(self, institution, loan_id):
        with self.sf() as session:
            row = session.scalar(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution, PhysicalLoanRow.id == loan_id))
            return self._loan(row) if row else None

    def loans(self, institution, borrower=None):
        with self.sf() as session:
            stmt = select(PhysicalLoanRow).where(PhysicalLoanRow.institution_id == institution)
            if borrower is not None:
                stmt = stmt.where(PhysicalLoanRow.borrower_account_id == borrower)
            return tuple(self._loan(r) for r in session.scalars(
                stmt.order_by(PhysicalLoanRow.borrowed_at.desc()).limit(250)).all())

    def eligible_renewal_ids(self, institution, borrower, now):
        # Full active set, not paginated. Never infer a policy decision from the
        # first 250 loans shown on screen.
        with self.sf() as session:
            policy = self._policy(session, institution)
            active = session.scalars(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.borrower_account_id == borrower,
                PhysicalLoanRow.returned_at.is_(None))).all()
            if any(_aware(row.due_at) <= now for row in active):
                return frozenset()
            return frozenset(row.id for row in active if row.renewal_count < policy.max_renewals)

    def renew_loan(self, institution, loan_id, borrower, version, now):
        with self.sf.begin() as session:
            self._lock_borrower(session, institution, borrower)
            self._lock_policy(session, institution)
            policy = self._policy(session, institution)
            current = session.scalar(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.id == loan_id,
                PhysicalLoanRow.borrower_account_id == borrower).with_for_update())
            if current is None:
                # A foreign borrower's loan must not be disclosed to the caller.
                raise ValueError('campus_library_loan_not_found')
            if current.row_version != version or current.returned_at is not None:
                raise ValueError('campus_library_loan_concurrent_modification')
            if _aware(current.due_at) <= now:
                raise ValueError('campus_library_loan_overdue_no_renewal')
            if current.renewal_count >= policy.max_renewals:
                raise ValueError('campus_library_renewal_limit_reached')
            # No renewal when another borrowed volume is already overdue.
            if session.scalar(select(PhysicalLoanRow.id).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.borrower_account_id == borrower,
                PhysicalLoanRow.id != loan_id,
                PhysicalLoanRow.returned_at.is_(None),
                PhysicalLoanRow.due_at <= now).limit(1)) is not None:
                raise ValueError('campus_library_overdue_loans_block_renewal')
            current.due_at += timedelta(days=policy.renewal_days)
            current.renewal_count += 1
            current.last_renewed_at = now
            current.row_version += 1
            session.flush()
            return self._loan(current)

    def return_loan(self, institution, loan_id, version, now):
        with self.sf.begin() as session:
            current = session.scalar(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.id == loan_id).with_for_update())
            if current is None or current.row_version != version or current.returned_at is not None:
                raise ValueError('campus_library_loan_not_found_or_concurrent_modification')
            # No modifications to a previous successful return; row_version is monotonic.
            current.returned_at = now
            current.closure_reason = 'returned'
            current.row_version += 1
            session.flush()
            return self._loan(current)


    def close_loan_with_incident(self, institution, loan_id, version, condition, now):
        """Atomic lost/damaged resolution: loan closes AND copy leaves circulation.

        A stale version cannot close a new loan or reactivate an invalid copy.
        Locks are scoped by tenant and verified in a single transaction.
        """
        if condition not in ('lost', 'damaged'):
            raise ValueError('campus_library_incident_invalid')
        with self.sf.begin() as session:
            current = session.scalar(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.id == loan_id).with_for_update())
            if current is None or current.row_version != version or current.returned_at is not None:
                raise ValueError('campus_library_loan_not_found_or_concurrent_modification')
            copy = session.scalar(select(PhysicalCopyRow).where(
                PhysicalCopyRow.institution_id == institution,
                PhysicalCopyRow.id == current.copy_id).with_for_update())
            if copy is None or not copy.active or copy.condition != 'serviceable':
                raise ValueError('campus_library_copy_unavailable')
            current.returned_at = now
            current.closure_reason = condition
            current.row_version += 1
            copy.active = False
            copy.condition = condition
            copy.row_version += 1
            session.flush()
            return self._loan(current)

    def restore_damaged_copy(self, institution, copy_id, version):
        """Only repaired, quarantined DAMAGED copies can be returned to inventory."""
        with self.sf.begin() as session:
            copy = session.scalar(select(PhysicalCopyRow).where(
                PhysicalCopyRow.institution_id == institution,
                PhysicalCopyRow.id == copy_id).with_for_update())
            if copy is None or copy.row_version != version:
                raise ValueError('campus_library_copy_concurrent_modification')
            if copy.condition != 'damaged' or copy.active:
                raise ValueError('campus_library_copy_not_restorable')
            open_loan = session.scalar(select(PhysicalLoanRow.id).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.copy_id == copy_id,
                PhysicalLoanRow.returned_at.is_(None)).limit(1))
            if open_loan is not None:
                raise ValueError('campus_library_copy_unavailable')
            copy.condition = 'serviceable'
            copy.active = True
            copy.row_version += 1
            session.flush()
            return self._copy(copy)
