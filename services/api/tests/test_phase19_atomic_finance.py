"""Integration-level checks for atomic finance posting using SQLite.

PostgreSQL concurrent locking tests are still required for certification.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.shared.infrastructure.database import Base
from app.modules.student_finance.domain.model import FinanceReceipt
from app.modules.student_finance.infrastructure.sqlalchemy_repo import (
    FinanceLedgerRow, FinanceReceiptRow, StudentChargeRow,
    SqlStudentFinanceRepository,
)


@pytest.fixture
def database():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    with sf.begin() as s:
        s.add(StudentChargeRow(
            id="charge-1", institution_id="institution-a",
            student_id="student-a", registration_id="registration-a",
            fee_item_id="fee-1", code="FEE", label="Tuition",
            amount_minor=5000, paid_minor=0, currency="CDF",
            due_on=None, state="open",
            created_at=datetime(2026, 10, 30, tzinfo=UTC),
        ))
    try:
        yield sf, SqlStudentFinanceRepository(sf)
    finally:
        engine.dispose()


def receipt(external_reference="provider-ref"):
    rid = uuid4().hex
    return FinanceReceipt(
        rid, "institution-a", "student-a", "RCT-" + rid[:12],
        2500, "CDF", "mobile_money", external_reference,
        "provider:sandbox", datetime(2026, 10, 30, tzinfo=UTC), False,
    )


def test_atomic_payment_posts_receipt_charge_and_ledger_together(database):
    sf, repo = database
    posted = repo.post_payment_atomic(receipt(), "provider callback")
    with sf() as s:
        charge = s.get(StudentChargeRow, "charge-1")
        ledger = s.scalars(select(FinanceLedgerRow)).all()
        receipts = s.scalars(select(FinanceReceiptRow)).all()
        assert posted.id == receipts[0].id
        assert charge.paid_minor == 2500
        assert len(ledger) == len(receipts) == 1
        assert ledger[0].amount_minor == 2500


def test_atomic_payment_rolls_back_when_ledger_insert_fails(database):
    sf, repo = database

    def fail_ledger(mapper, connection, target):
        raise RuntimeError("injected_ledger_failure")

    event.listen(FinanceLedgerRow, "before_insert", fail_ledger)
    try:
        with pytest.raises(RuntimeError, match="injected_ledger_failure"):
            repo.post_payment_atomic(receipt(), "provider callback")
    finally:
        event.remove(FinanceLedgerRow, "before_insert", fail_ledger)

    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 0
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 0
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 0


def test_atomic_payment_replay_does_not_allocate_twice(database):
    sf, repo = database
    first = repo.post_payment_atomic(receipt(), "provider callback")
    second = repo.post_payment_atomic(receipt(), "provider callback retry")
    assert second.id == first.id
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 2500
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 1
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 1


def test_atomic_payment_spreads_amount_over_multiple_charges(database):
    sf, repo = database
    with sf.begin() as s:
        s.add(StudentChargeRow(
            id="charge-2", institution_id="institution-a",
            student_id="student-a", registration_id="registration-a",
            fee_item_id="fee-2", code="SECOND", label="Second fee",
            amount_minor=4000, paid_minor=0, currency="CDF",
            due_on=None, state="open",
            created_at=datetime(2026, 10, 30, tzinfo=UTC),
        ))
    first = receipt("multi-charge-ref")
    from dataclasses import replace
    first = replace(first, amount_minor=7000)
    repo.post_payment_atomic(first, "multiple charges")
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 5000
        assert s.get(StudentChargeRow, "charge-2").paid_minor == 2000
        rows = s.scalars(select(FinanceLedgerRow).order_by(FinanceLedgerRow.charge_id)).all()
        assert [row.amount_minor for row in rows] == [5000, 2000]
        assert all(row.reference == first.reference for row in rows)


def test_atomic_payment_rejects_overpayment_without_partial_writes(database):
    sf, repo = database
    from dataclasses import replace
    excessive = replace(receipt("overpayment-ref"), amount_minor=5001)
    with pytest.raises(
        ValueError, match="finance_overpayment_requires_explicit_credit_policy"
    ):
        repo.post_payment_atomic(excessive, "excessive amount")
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 0
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 0
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 0


def test_atomic_payment_conflicting_reference_preserves_first_settlement(database):
    sf, repo = database
    first = repo.post_payment_atomic(receipt("shared-provider-ref"), "first")
    from dataclasses import replace
    conflicting = replace(receipt("shared-provider-ref"), amount_minor=1000)
    with pytest.raises(ValueError, match="finance_external_reference_conflict"):
        repo.post_payment_atomic(conflicting, "conflict")
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 2500
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 1
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 1
