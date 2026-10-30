"""SQL transaction regression checks; PostgreSQL concurrency tests remain required."""
from datetime import UTC, datetime
from hashlib import sha256
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.shared.infrastructure.database import Base
from app.modules.payment_gateway.infrastructure.sqlalchemy_repo import (
    PaymentIntentRow, ProviderEventRow, SqlPaymentGatewayRepository,
)
from app.modules.student_finance.infrastructure.sqlalchemy_repo import (
    FinanceLedgerRow, FinanceReceiptRow, StudentChargeRow,
    SqlStudentFinanceRepository,
)


@pytest.fixture
def repositories():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    now = datetime(2026, 10, 30, tzinfo=UTC)
    with sf.begin() as s:
        s.add(PaymentIntentRow(
            id="intent-1", institution_id="institution-a",
            student_id="student-a", amount_minor=2500,
            currency="CDF", provider="sandbox", payer_msisdn="+243810000001",
            idempotency_key="key-1", merchant_reference="PAY-1",
            provider_reference=None, status="pending", created_by="student-a",
            created_at=now, updated_at=now, expires_at=now,
            failure_code=None, receipt_id=None,
        ))
        s.add(StudentChargeRow(
            id="charge-1", institution_id="institution-a",
            student_id="student-a", registration_id="registration-a",
            fee_item_id="fee-1", code="TUITION", label="Tuition",
            amount_minor=5000, paid_minor=0, currency="CDF",
            due_on=None, state="open", created_at=now,
        ))
    try:
        yield sf, SqlPaymentGatewayRepository(sf), SqlStudentFinanceRepository(sf), now
    finally:
        engine.dispose()


def settle(gateway, finance, now, event_id="event-1"):
    return gateway.settle_callback_atomic(
        "sandbox", event_id, "intent-1", "succeeded",
        "provider-ref-1", sha256(b"same-payload").hexdigest(),
        None, finance, now,
    )


def test_callback_settlement_commits_finance_and_provider_state(repositories):
    sf, gateway, finance, now = repositories
    result = settle(gateway, finance, now)
    assert result.status.value == "succeeded"
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 2500
        assert s.get(PaymentIntentRow, "intent-1").receipt_id == result.receipt_id
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 1
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 1
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1
        assert s.scalar(select(ProviderEventRow.processed)) is True


def test_callback_settlement_rollback_on_ledger_failure(repositories):
    sf, gateway, finance, now = repositories

    def fail_ledger(mapper, connection, target):
        raise RuntimeError("injected_callback_ledger_failure")

    event.listen(FinanceLedgerRow, "before_insert", fail_ledger)
    try:
        with pytest.raises(RuntimeError, match="injected_callback_ledger_failure"):
            settle(gateway, finance, now)
    finally:
        event.remove(FinanceLedgerRow, "before_insert", fail_ledger)

    with sf() as s:
        assert s.get(PaymentIntentRow, "intent-1").status == "pending"
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 0
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 0
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 0
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 0


def test_callback_exact_replay_does_not_duplicate_settlement(repositories):
    sf, gateway, finance, now = repositories
    first = settle(gateway, finance, now)
    again = settle(gateway, finance, now)
    assert first.receipt_id == again.receipt_id
    with sf() as s:
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 2500
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 1
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 1
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1


def test_failed_callback_commits_no_finance_receipt(repositories):
    sf, gateway, finance, now = repositories
    result = gateway.settle_callback_atomic(
        "sandbox", "failed-event", "intent-1", "failed",
        "provider-failed-ref", sha256(b"failed").hexdigest(),
        "provider_rejected", finance, now,
    )
    assert result.status.value == "failed"
    assert result.failure_code == "provider_rejected"
    with sf() as s:
        assert s.get(PaymentIntentRow, "intent-1").status == "failed"
        assert s.get(StudentChargeRow, "charge-1").paid_minor == 0
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 0
        assert s.scalar(select(func.count()).select_from(FinanceLedgerRow)) == 0
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1


def test_atomic_callback_rejects_different_session_factory(repositories):
    sf, gateway, finance, now = repositories
    finance.sf = sessionmaker(bind=sf.kw["bind"])
    with pytest.raises(RuntimeError, match="payment_finance_session_factory_mismatch"):
        settle(gateway, finance, now)
    with sf() as s:
        assert s.get(PaymentIntentRow, "intent-1").status == "pending"
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 0


def test_atomic_callback_conflicting_event_digest_is_rejected(repositories):
    sf, gateway, finance, now = repositories
    settle(gateway, finance, now)
    with pytest.raises(PermissionError, match="payment_provider_event_replay_conflict"):
        gateway.settle_callback_atomic(
            "sandbox", "event-1", "intent-1", "succeeded",
            "provider-ref-1", sha256(b"tampered").hexdigest(),
            None, finance, now,
        )
    with sf() as s:
        assert s.scalar(select(func.count()).select_from(FinanceReceiptRow)) == 1
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1
