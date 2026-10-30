"""Real simultaneous transactions; opt-in on the dedicated local PostgreSQL DB."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import os
from threading import Barrier, Event
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from test_phase19_atomic_callback import repositories, settle
from test_phase19_atomic_finance import database, receipt
from app.modules.payment_gateway.infrastructure.sqlalchemy_repo import PaymentIntentRow, ProviderEventRow
from app.modules.student_finance.infrastructure.sqlalchemy_repo import StudentChargeRow, FinanceReceiptRow, FinanceLedgerRow

pytestmark = pytest.mark.skipif(not os.getenv('EDUNOVA_FINANCE_TEST_DATABASE_URL'), reason='Requires dedicated real PostgreSQL on localhost:55439')


def simultaneous(*actions):
    barrier = Barrier(len(actions))
    def invoke(action):
        barrier.wait(timeout=10)
        try:
            return action()
        except Exception as exc:
            return exc
    with ThreadPoolExecutor(max_workers=len(actions)) as executor:
        futures = [executor.submit(invoke, action) for action in actions]
        return [future.result(timeout=30) for future in futures]


def counts(sf):
    with sf() as s:
        return tuple(s.scalar(select(func.count()).select_from(model)) for model in (FinanceReceiptRow, FinanceLedgerRow))


def test_concurrent_identical_callbacks_settle_once(repositories):
    sf, gateway, finance, now = repositories
    results = simultaneous(*[lambda: settle(gateway, finance, now) for _ in range(4)])
    assert not any(isinstance(result, Exception) for result in results), results
    assert len({result.receipt_id for result in results}) == 1
    assert counts(sf) == (1, 1)
    with sf() as s:
        assert s.get(StudentChargeRow, 'charge-1').paid_minor == 2500
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1


def test_concurrent_modified_callback_rejected(repositories):
    sf, gateway, finance, now = repositories
    def tampered():
        return gateway.settle_callback_atomic('sandbox', 'event-1', 'intent-1', 'succeeded', 'provider-ref-1', sha256(b'tampered').hexdigest(), None, finance, now)
    results = simultaneous(lambda: settle(gateway, finance, now), tampered)
    assert sum(isinstance(result, PermissionError) for result in results) == 1, results
    assert counts(sf) == (1, 1)


def test_concurrent_distinct_payments_do_not_lose_allocation(database):
    sf, finance = database
    results = simultaneous(*[lambda n=n: finance.post_payment_atomic(receipt(f'provider-{n}'), 'concurrent') for n in range(2)])
    assert not any(isinstance(result, Exception) for result in results), results
    assert counts(sf) == (2, 2)
    with sf() as s:
        assert s.get(StudentChargeRow, 'charge-1').paid_minor == 5000


def test_concurrent_conflicting_reference_preserves_one_payment(database):
    sf, finance = database
    results = simultaneous(lambda: finance.post_payment_atomic(receipt('conflict'), 'first'), lambda: finance.post_payment_atomic(replace(receipt('conflict'), amount_minor=1000), 'second'))
    errors = [result for result in results if isinstance(result, Exception)]
    assert len(errors) == 1 and str(errors[0]) == 'finance_external_reference_conflict', results
    assert counts(sf) == (1, 1)
    with sf() as s:
        assert s.get(StudentChargeRow, 'charge-1').paid_minor in (1000, 2500)


@pytest.mark.parametrize('terminal', ['expired', 'cancelled'])
def test_callback_racing_stale_terminal_save_cannot_erase_settlement(repositories, terminal):
    sf, gateway, finance, now = repositories
    from app.modules.payment_gateway.application.service import PaymentGatewayService
    read, committed = Event(), Event()
    original_get = gateway.get
    def delayed_get(intent_id):
        stale = original_get(intent_id)
        read.set()
        assert committed.wait(timeout=15)
        return stale
    gateway.get = delayed_get
    service = PaymentGatewayService(gateway, Mock(), Mock(), Mock(), lambda: now)
    def callback():
        assert read.wait(timeout=15)
        try:
            return settle(gateway, finance, now)
        finally:
            committed.set()
    operation = (lambda: service.expire('intent-1')) if terminal == 'expired' else (lambda: service.cancel('student-a', 'institution-a', 'intent-1', 'test cancellation'))
    results = simultaneous(callback, operation)
    assert not isinstance(results[0], Exception), results
    assert isinstance(results[1], ValueError) and str(results[1]) == 'payment_terminal_status_conflict', results
    with sf() as s:
        intent = s.get(PaymentIntentRow, 'intent-1')
        receipts, ledger = counts(sf)
        if receipts:
            assert intent.status == 'succeeded' and intent.receipt_id is not None, (terminal, intent.status, results)
            assert receipts == ledger == 1
        else:
            assert intent.status == terminal
            assert ledger == 0


@pytest.mark.parametrize('terminal', ['expired', 'cancelled'])
def test_terminal_operation_committed_first_blocks_callback(repositories, terminal):
    sf, gateway, finance, now = repositories
    from app.modules.payment_gateway.application.service import PaymentGatewayService
    service = PaymentGatewayService(gateway, Mock(), Mock(), Mock(), lambda: now)
    if terminal == 'expired':
        service.expire('intent-1')
    else:
        service.cancel('student-a', 'institution-a', 'intent-1', 'test cancellation')
    with pytest.raises(ValueError, match='payment_terminal_status_conflict'):
        settle(gateway, finance, now)
    assert counts(sf) == (0, 0)
    with sf() as s:
        assert s.get(PaymentIntentRow, 'intent-1').status == terminal
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 0


def test_provider_reference_conflict_rolls_back_second_intent(repositories):
    sf, gateway, finance, now = repositories
    second = replace(gateway.get('intent-1'), id='intent-2', merchant_reference='PAY-2', idempotency_key='key-2')
    gateway.save(second)
    settle(gateway, finance, now)
    with pytest.raises(IntegrityError):
        gateway.settle_callback_atomic('sandbox', 'event-2', 'intent-2', 'succeeded', 'provider-ref-1', sha256(b'second').hexdigest(), None, finance, now)
    assert counts(sf) == (1, 1)
    with sf() as s:
        second = s.get(PaymentIntentRow, 'intent-2')
        assert second.status == 'pending' and second.receipt_id is None
        assert s.get(StudentChargeRow, 'charge-1').paid_minor == 2500
        assert s.scalar(select(func.count()).select_from(ProviderEventRow)) == 1
