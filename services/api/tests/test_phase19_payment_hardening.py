"""Regression coverage for Phase 19 payment gateway hardening.

These tests use isolated fakes and require no database or provider credentials.
"""
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.modules.payment_gateway.application.service import PaymentGatewayService


def service():
    repo = Mock()
    finance = Mock()
    students = Mock()
    students.get.return_value = SimpleNamespace(
        institution_id="institution-a", account_id="student-a"
    )
    finance.statement.return_value = {
        "balances_by_currency": {"CDF": 10000}
    }
    gateway = PaymentGatewayService(
        repo=repo,
        finance=finance,
        student_repo=students,
        campus=Mock(),
        now=lambda: datetime(2026, 10, 30, tzinfo=UTC),
        secrets={"sandbox": "test-only-secret"},
    )
    return gateway, repo, finance


def test_idempotency_key_cannot_be_reused_with_another_payer():
    gateway, repo, finance = service()
    repo.by_idempotency.return_value = SimpleNamespace(
        student_id="student-1",
        amount_minor=2500,
        currency="CDF",
        provider="sandbox",
        payer_msisdn="+243810000001",
    )

    with pytest.raises(ValueError, match="payment_idempotency_conflict"):
        gateway.initiate(
            "student-a", "institution-a", "student-1", 2500,
            "CDF", "sandbox", "+243810000002", "same-key"
        )

    repo.save.assert_not_called()
    finance.payment.assert_not_called()


def test_invalid_signed_callback_does_not_record_provider_event():
    gateway, repo, finance = service()
    envelope = {
        "event_id": "event-1",
        "intent_id": "intent-1",
        "status": "unknown",
        "provider_reference": None,
        "payload": {},
    }
    import json
    raw = json.dumps(
        envelope, sort_keys=True, separators=(",", ":")
    ).encode()
    signature = gateway.sign_sandbox(raw)

    with pytest.raises(ValueError, match="payment_callback_status_invalid"):
        gateway.callback(
            "sandbox", "event-1", "intent-1", "unknown",
            None, {}, signature
        )

    repo.add_event.assert_not_called()
    repo.add_attempt.assert_not_called()
    finance.payment.assert_not_called()


def test_invalid_signature_cannot_create_payment_or_provider_event():
    gateway, repo, finance = service()

    with pytest.raises(PermissionError, match="payment_callback_signature_invalid"):
        gateway.callback(
            "sandbox", "event-2", "intent-2", "succeeded",
            "provider-ref-2", {}, "invalid-signature"
        )

    repo.event.assert_not_called()
    repo.add_event.assert_not_called()
    repo.add_attempt.assert_not_called()
    finance.payment.assert_not_called()


def test_identical_callback_replay_does_not_create_another_receipt():
    gateway, repo, finance = service()
    import hashlib
    import json
    envelope = {
        "event_id": "event-3",
        "intent_id": "intent-3",
        "status": "succeeded",
        "provider_reference": "provider-ref-3",
        "payload": {},
    }
    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    repo.event.return_value = SimpleNamespace(
        payment_intent_id="intent-3",
        payload_sha256=hashlib.sha256(raw).hexdigest(),
    )
    existing_intent = SimpleNamespace(id="intent-3")
    repo.get.return_value = existing_intent

    result = gateway.callback(
        "sandbox", "event-3", "intent-3", "succeeded",
        "provider-ref-3", {}, gateway.sign_sandbox(raw)
    )

    assert result is existing_intent
    repo.add_event.assert_not_called()
    repo.add_attempt.assert_not_called()
    finance.payment.assert_not_called()


def test_replay_with_modified_payload_is_rejected():
    gateway, repo, finance = service()
    repo.event.return_value = SimpleNamespace(
        payment_intent_id="intent-4",
        payload_sha256="different-digest",
    )
    import json
    raw = json.dumps(
        {
            "event_id": "event-4",
            "intent_id": "intent-4",
            "status": "succeeded",
            "provider_reference": None,
            "payload": {},
        },
        sort_keys=True, separators=(",", ":")
    ).encode()

    with pytest.raises(PermissionError, match="payment_provider_event_replay_conflict"):
        gateway.callback(
            "sandbox", "event-4", "intent-4", "succeeded",
            None, {}, gateway.sign_sandbox(raw)
        )

    repo.add_event.assert_not_called()
    finance.payment.assert_not_called()


def test_student_from_another_institution_cannot_start_payment():
    gateway, repo, finance = service()
    gateway.student_repo.get.return_value = SimpleNamespace(
        institution_id="institution-b", account_id="student-a"
    )

    with pytest.raises(ValueError, match="payment_student_not_found"):
        gateway.initiate(
            "student-a", "institution-a", "student-1", 2500,
            "CDF", "sandbox", "+243810000001", "cross-campus-key"
        )

    repo.by_idempotency.assert_not_called()
    repo.save.assert_not_called()
    finance.payment.assert_not_called()


def test_provider_observation_does_not_settle_payment():
    gateway, repo, finance = service()
    from app.modules.payment_gateway.domain.model import PaymentStatus
    repo.get.return_value = SimpleNamespace(
        id="intent-5", institution_id="institution-a",
        status=PaymentStatus.PENDING, provider="sandbox"
    )
    repo.next_attempt_no.return_value = 1

    result = gateway.record_poll(
        "finance-admin", "institution-a", "intent-5",
        provider_status="succeeded", provider_reference="external-5"
    )

    assert result.kind == "poll"
    assert result.outcome == "succeeded"
    repo.add_attempt.assert_called_once()
    repo.save.assert_not_called()
    finance.payment.assert_not_called()


def test_cross_institution_provider_observation_is_rejected():
    gateway, repo, finance = service()
    from app.modules.payment_gateway.domain.model import PaymentStatus
    repo.get.return_value = SimpleNamespace(
        id="intent-6", institution_id="institution-b",
        status=PaymentStatus.PENDING, provider="sandbox"
    )

    with pytest.raises(ValueError, match="payment_intent_not_found"):
        gateway.record_poll(
            "finance-admin", "institution-a", "intent-6",
            provider_status="succeeded"
        )

    repo.add_attempt.assert_not_called()
    repo.save.assert_not_called()
    finance.payment.assert_not_called()


def test_finance_external_reference_cannot_be_reused_for_another_student():
    from app.modules.student_finance.application.service import StudentFinanceService

    repo = Mock()
    repo.receipt_by_external.return_value = SimpleNamespace(
        student_id="student-a",
        amount_minor=2500,
        currency="CDF",
        method="mobile_money",
    )
    student_repo = Mock()
    student_repo.get.return_value = SimpleNamespace(
        institution_id="institution-a"
    )
    finance = StudentFinanceService(
        repo=repo,
        campus=Mock(),
        campus_repo=Mock(),
        student_repo=student_repo,
        now=lambda: datetime(2026, 10, 30, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="finance_external_reference_conflict"):
        finance.payment(
            "provider:sandbox", "institution-a", "student-b",
            2500, "CDF", "mobile_money", "provider-reference-1",
            internal=True,
        )

    repo.add_receipt.assert_not_called()
    repo.update_charge_paid.assert_not_called()
    repo.add_ledger.assert_not_called()


def test_finance_external_reference_replay_returns_matching_receipt():
    from app.modules.student_finance.application.service import StudentFinanceService

    repo = Mock()
    receipt = SimpleNamespace(
        student_id="student-a",
        amount_minor=2500,
        currency="CDF",
        method="mobile_money",
    )
    repo.receipt_by_external.return_value = receipt
    student_repo = Mock()
    student_repo.get.return_value = SimpleNamespace(
        institution_id="institution-a"
    )
    finance = StudentFinanceService(
        repo=repo,
        campus=Mock(),
        campus_repo=Mock(),
        student_repo=student_repo,
        now=lambda: datetime(2026, 10, 30, tzinfo=UTC),
    )

    result = finance.payment(
        "provider:sandbox", "institution-a", "student-a",
        2500, "CDF", "mobile_money", "provider-reference-1",
        internal=True,
    )

    assert result is receipt
    repo.add_receipt.assert_not_called()
    repo.add_ledger.assert_not_called()
