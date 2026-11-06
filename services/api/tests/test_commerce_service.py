from datetime import UTC, datetime, timedelta

import pytest

from app.modules.commerce.application.service import CommerceService
from app.modules.commerce.domain.model import Money, PaymentState, Plan, WebhookEvent
from app.modules.commerce.infrastructure.memory import (
    FakeMobileMoneyProvider,
    InMemoryAiWalletRepository,
    InMemoryEntitlementRepository,
    InMemoryPaymentRepository,
    InMemoryReceiptRepository,
    InMemoryWebhookInbox,
    InMemoryCommerceSettlement,
    StaticPlanCatalog,
)


class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    def __call__(self): return self.value
    def advance(self, **kwargs): self.value += timedelta(**kwargs)


def make_service(price=3000, credits=25):
    clock = Clock()
    payments = InMemoryPaymentRepository()
    entitlements = InMemoryEntitlementRepository()
    wallets = InMemoryAiWalletRepository()
    receipts = InMemoryReceiptRepository()
    inbox = InMemoryWebhookInbox()
    catalog = StaticPlanCatalog([Plan(code="premium-30d", name="Premium", price=Money(price), included_ai_credits=credits)])
    provider = FakeMobileMoneyProvider()
    settlement = InMemoryCommerceSettlement(payments=payments, entitlements=entitlements, wallets=wallets, receipts=receipts, inbox=inbox)
    service = CommerceService(payments=payments, entitlements=entitlements, wallets=wallets, receipts=receipts, inbox=inbox, catalog=catalog, providers={provider.name: provider}, settlement=settlement, now=clock)
    return service, clock, provider, payments, entitlements, wallets, receipts


def checkout(service, key="idem-key-001", account="a1"):
    return service.create_checkout(account_id=account, plan_code="premium-30d", phone_number="+243999000111", idempotency_key=key, provider_name="sandbox-mobile-money")


def success_event(payment, clock, event_id="evt-1"):
    return WebhookEvent(provider=payment.provider, event_id=event_id, provider_reference=payment.provider_reference or "", state=PaymentState.SUCCEEDED, amount=payment.amount, received_at=clock())


def test_checkout_is_idempotent():
    service, *_ = make_service()
    first = checkout(service)
    second = checkout(service)
    assert first.payment.id == second.payment.id
    assert first.payment.provider_reference == second.payment.provider_reference


def test_success_activates_30_days_grants_ai_and_one_receipt():
    service, clock, _, _, entitlements, wallets, receipts = make_service()
    result = checkout(service)
    service.process_webhook(provider_name=result.payment.provider, event=success_event(result.payment, clock))
    entitlement = entitlements.get("a1")
    assert entitlement.is_premium(clock())
    assert entitlement.premium_until == clock() + timedelta(days=30)
    assert wallets.get("a1").balance == 25
    assert len(receipts.list_for_account("a1")) == 1


def test_duplicate_webhook_cannot_double_activate_or_double_grant():
    service, clock, _, _, entitlements, wallets, receipts = make_service()
    result = checkout(service)
    event = success_event(result.payment, clock)
    service.process_webhook(provider_name=result.payment.provider, event=event)
    first_expiry = entitlements.get("a1").premium_until
    service.process_webhook(provider_name=result.payment.provider, event=event)
    assert entitlements.get("a1").premium_until == first_expiry
    assert wallets.get("a1").balance == 25
    assert len(receipts.list_for_account("a1")) == 1


def test_early_renewal_preserves_remaining_days():
    service, clock, _, _, entitlements, wallets, _ = make_service()
    p1 = checkout(service, "idem-key-001").payment
    service.process_webhook(provider_name=p1.provider, event=success_event(p1, clock, "evt-1"))
    first_expiry = entitlements.get("a1").premium_until
    clock.advance(days=10)
    p2 = checkout(service, "idem-key-002").payment
    service.process_webhook(provider_name=p2.provider, event=success_event(p2, clock, "evt-2"))
    assert entitlements.get("a1").premium_until == first_expiry + timedelta(days=30)
    assert wallets.get("a1").balance == 25


def test_amount_mismatch_is_rejected_without_entitlement():
    service, clock, *_ = make_service()
    p = checkout(service).payment
    forged = WebhookEvent(provider=p.provider, event_id="forged", provider_reference=p.provider_reference or "", state=PaymentState.SUCCEEDED, amount=Money(4000), received_at=clock())
    with pytest.raises(ValueError, match="payment_amount_mismatch"):
        service.process_webhook(provider_name=p.provider, event=forged)
    assert not service.snapshot("a1").premium


def test_reversal_of_latest_payment_suspends_but_old_reversal_does_not_cancel_newer_renewal():
    service, clock, *_ = make_service()
    p1 = checkout(service, "idem-key-001").payment
    service.process_webhook(provider_name=p1.provider, event=success_event(p1, clock, "evt-1"))
    p2 = checkout(service, "idem-key-002").payment
    service.process_webhook(provider_name=p2.provider, event=success_event(p2, clock, "evt-2"))
    old_reversal = WebhookEvent(provider=p1.provider, event_id="rev-old", provider_reference=p1.provider_reference or "", state=PaymentState.REVERSED, amount=p1.amount, received_at=clock())
    service.process_webhook(provider_name=p1.provider, event=old_reversal)
    assert service.snapshot("a1").premium
    latest_reversal = WebhookEvent(provider=p2.provider, event_id="rev-new", provider_reference=p2.provider_reference or "", state=PaymentState.REVERSED, amount=p2.amount, received_at=clock())
    service.process_webhook(provider_name=p2.provider, event=latest_reversal)
    assert not service.snapshot("a1").premium


def test_ai_wallet_cannot_go_negative():
    service, clock, *_ = make_service(credits=3)
    p = checkout(service).payment
    service.process_webhook(provider_name=p.provider, event=success_event(p, clock))
    assert service.consume_ai_credits(account_id="a1", credits=2) == 1
    with pytest.raises(ValueError, match="insufficient_ai_credits"):
        service.consume_ai_credits(account_id="a1", credits=2)


def test_offline_entitlement_snapshot_never_extends_beyond_72_hours_or_subscription_expiry():
    service, clock, *_ = make_service()
    p = checkout(service).payment
    service.process_webhook(provider_name=p.provider, event=success_event(p, clock))
    snap = service.snapshot("a1")
    assert snap.valid_until == clock() + timedelta(hours=72)
    clock.advance(days=29, hours=23)
    snap2 = service.snapshot("a1")
    assert snap2.valid_until == snap2.premium_until

def test_purchased_ai_credits_survive_new_premium_cycle():
    service, clock, _, _, _, wallets, _ = make_service(credits=25)
    wallet = wallets.get('a1')
    wallet.grant_purchased(10, clock())
    wallets.save(wallet)
    p = checkout(service).payment
    service.process_webhook(provider_name=p.provider, event=success_event(p, clock))
    updated = wallets.get('a1')
    assert updated.included_balance == 25
    assert updated.purchased_balance == 10
    assert updated.balance == 35

def test_ai_pack_adds_purchased_credits_without_extending_premium():
    clock = Clock()
    payments = InMemoryPaymentRepository(); entitlements = InMemoryEntitlementRepository(); wallets = InMemoryAiWalletRepository(); receipts = InMemoryReceiptRepository(); inbox = InMemoryWebhookInbox()
    pack = Plan(code='ai-pack-10', name='Pack IA 10', price=Money(500), kind='ai_pack', duration_days=0, included_ai_credits=10, max_personal_documents=0, offline_enabled=False)
    catalog = StaticPlanCatalog([pack]); provider = FakeMobileMoneyProvider(); settlement = InMemoryCommerceSettlement(payments=payments, entitlements=entitlements, wallets=wallets, receipts=receipts, inbox=inbox)
    service = CommerceService(payments=payments, entitlements=entitlements, wallets=wallets, receipts=receipts, inbox=inbox, catalog=catalog, providers={provider.name:provider}, settlement=settlement, now=clock)
    result = service.create_checkout(account_id='a1', plan_code='ai-pack-10', phone_number='+243999', idempotency_key='pack-idem-1', provider_name=provider.name)
    service.process_webhook(provider_name=provider.name, event=success_event(result.payment, clock, 'pack-event'))
    assert not entitlements.get('a1').is_premium(clock())
    assert wallets.get('a1').purchased_balance == 10


def test_idempotency_key_cannot_be_reused_for_different_checkout():
    service, *_ = make_service()
    checkout(service, key="same-key-0001")
    with pytest.raises(ValueError, match="idempotency_key_conflict"):
        service.create_checkout(account_id="a1", plan_code="premium-30d", phone_number="+243888000222", idempotency_key="same-key-0001", provider_name="sandbox-mobile-money")


def test_reversing_latest_renewal_falls_back_to_previous_paid_period():
    service, clock, _, _, entitlements, _, _ = make_service()
    p1 = checkout(service, "idem-ledger-1").payment
    service.process_webhook(provider_name=p1.provider, event=success_event(p1, clock, "ledger-success-1"))
    first_expiry = entitlements.get("a1").premium_until
    p2 = checkout(service, "idem-ledger-2").payment
    service.process_webhook(provider_name=p2.provider, event=success_event(p2, clock, "ledger-success-2"))
    assert entitlements.get("a1").premium_until == first_expiry + timedelta(days=30)
    reversal = WebhookEvent(provider=p2.provider,event_id="ledger-reversal-2",provider_reference=p2.provider_reference or "",state=PaymentState.REVERSED,amount=p2.amount,received_at=clock())
    service.process_webhook(provider_name=p2.provider, event=reversal)
    assert entitlements.get("a1").premium_until == first_expiry
    assert entitlements.get("a1").is_premium(clock())


def test_expire_stale_checkouts_sweeps_only_open_expired_payments():
    service, clock, _, payments, _, _, _ = make_service()
    p = checkout(service, "stale-0001").payment
    assert p.state == PaymentState.PENDING
    clock.advance(minutes=16)
    assert service.expire_stale_checkouts() == 1
    assert payments.get(p.id).state == PaymentState.EXPIRED
    assert service.expire_stale_checkouts() == 0


def test_ai_credit_reservation_release_and_commit_are_accounted_safely():
    service, clock, _, _, _, wallets, _ = make_service(credits=5)
    p=checkout(service, 'reservation-sub').payment
    service.process_webhook(provider_name=p.provider,event=success_event(p,clock,'reservation-paid'))
    before=wallets.get('a1').balance
    r=service.reserve_ai_credits(account_id='a1',credits=2)
    assert wallets.get('a1').balance == before-2
    service.release_ai_reservation(r.id)
    assert wallets.get('a1').balance == before
    r2=service.reserve_ai_credits(account_id='a1',credits=2)
    service.commit_ai_reservation(r2.id)
    assert wallets.get('a1').balance == before-2
    assert wallets.get('a1').lifetime_spent >= 2
