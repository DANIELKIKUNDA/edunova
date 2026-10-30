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
