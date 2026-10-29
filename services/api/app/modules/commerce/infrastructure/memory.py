from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable
from uuid import uuid4

from app.modules.commerce.application.ports import ProviderPaymentStart
from app.modules.commerce.domain.model import (
    AiWallet,
    AiCreditReservation,
    AiReservationState,
    Entitlement,
    EntitlementState,
    Money,
    PaymentIntent,
    PaymentState,
    Plan,
    Receipt,
    SubscriptionGrant,
    WebhookEvent,
)


class InMemoryPaymentRepository:
    def __init__(self) -> None:
        self.items: dict[str, PaymentIntent] = {}

    def get(self, payment_id: str) -> PaymentIntent | None:
        return self.items.get(payment_id)

    def get_by_idempotency(self, account_id: str, key: str) -> PaymentIntent | None:
        return next((p for p in self.items.values() if p.account_id == account_id and p.idempotency_key == key), None)

    def get_by_provider_reference(self, provider: str, reference: str) -> PaymentIntent | None:
        return next((p for p in self.items.values() if p.provider == provider and p.provider_reference == reference), None)

    def list_open_expired(self, now, limit: int = 100) -> list[PaymentIntent]:
        return [p for p in self.items.values() if p.is_expired(now)][:limit]

    def save(self, payment: PaymentIntent) -> None:
        self.items[payment.id] = payment


class InMemoryEntitlementRepository:
    def __init__(self) -> None:
        self.items: dict[str, Entitlement] = {}

    def get(self, account_id: str) -> Entitlement:
        return self.items.setdefault(account_id, Entitlement(account_id=account_id))

    def save(self, entitlement: Entitlement) -> None:
        self.items[entitlement.account_id] = entitlement


class InMemoryAiWalletRepository:
    def __init__(self) -> None:
        self.items: dict[str, AiWallet] = {}

    def get(self, account_id: str) -> AiWallet:
        return self.items.setdefault(account_id, AiWallet(account_id=account_id))

    def save(self, wallet: AiWallet) -> None:
        self.items[wallet.account_id] = wallet


class InMemorySubscriptionGrantRepository:
    def __init__(self) -> None:
        self.items: dict[str, SubscriptionGrant] = {}

    def get_by_payment(self, payment_id: str) -> SubscriptionGrant | None:
        return next((g for g in self.items.values() if g.payment_id == payment_id), None)

    def list_for_account(self, account_id: str) -> list[SubscriptionGrant]:
        return sorted(
            [g for g in self.items.values() if g.account_id == account_id],
            key=lambda g: (g.granted_at, g.id),
        )

    def save(self, grant: SubscriptionGrant) -> None:
        self.items[grant.id] = grant


class InMemoryReceiptRepository:
    def __init__(self) -> None:
        self.items: list[Receipt] = []

    def save(self, receipt: Receipt) -> None:
        if not any(r.payment_id == receipt.payment_id for r in self.items):
            self.items.append(receipt)

    def list_for_account(self, account_id: str) -> list[Receipt]:
        return [r for r in self.items if r.account_id == account_id]


class InMemoryWebhookInbox:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    def has_seen(self, dedupe_key: str) -> bool:
        return dedupe_key in self.keys

    def mark_seen(self, event: WebhookEvent) -> None:
        self.keys.add(event.dedupe_key)


class StaticPlanCatalog:
    def __init__(self, plans: Iterable[Plan] | None = None) -> None:
        plans = plans or [
            Plan(
                code="premium-30d",
                name="Premium",
                price=Money(amount=3000),
                duration_days=30,
                included_ai_credits=25,
                max_personal_documents=100,
                offline_enabled=True,
            )
        ]
        self.items = {p.code: p for p in plans}

    def get(self, code: str) -> Plan | None:
        return self.items.get(code)

    def list(self) -> list[Plan]:
        return list(self.items.values())


class FakeMobileMoneyProvider:
    name = "sandbox-mobile-money"

    def __init__(self) -> None:
        self.created: dict[str, PaymentIntent] = {}

    def create_payment(self, payment: PaymentIntent) -> ProviderPaymentStart:
        reference = f"MM-{uuid4().hex[:16].upper()}"
        self.created[reference] = payment
        return ProviderPaymentStart(provider_reference=reference, action_type="prompt", action_value=None, user_message="Confirmez le paiement sur votre téléphone Mobile Money.")

    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> bool:
        return headers.get("x-edunova-sandbox-signature") == "valid"

    def parse_webhook(self, raw_body: bytes) -> WebhookEvent:
        data = json.loads(raw_body.decode())
        return WebhookEvent(
            provider=self.name,
            event_id=str(data["event_id"]),
            provider_reference=str(data["provider_reference"]),
            state=PaymentState(str(data["state"])),
            amount=Money(int(data["amount"]), str(data.get("currency", "CDF"))),
            received_at=datetime.fromisoformat(str(data["received_at"])),
        )

class InMemoryCommerceSettlement:
    def __init__(self, *, payments, entitlements, wallets, receipts, inbox, grants=None) -> None:
        self.payments = payments
        self.entitlements = entitlements
        self.wallets = wallets
        self.receipts = receipts
        self.inbox = inbox
        self.grants = grants or InMemorySubscriptionGrantRepository()
        self.ai_reservations: dict[str, AiCreditReservation] = {}

    def _recalculate_entitlement(self, account_id: str, now) -> None:
        ent = self.entitlements.get(account_id)
        active = [g for g in self.grants.list_for_account(account_id) if g.reversed_at is None]
        if not active:
            ent.premium_until = None
            ent.source_payment_id = None
            ent.state = EntitlementState.FREE
            ent.updated_at = now
            self.entitlements.save(ent)
            return
        # Grants are created sequentially. Reversal removes only the reversed grant;
        # the entitlement falls back to the latest remaining grant end.
        latest = max(active, key=lambda g: g.ends_at)
        ent.premium_until = latest.ends_at
        ent.source_payment_id = latest.payment_id
        ent.state = EntitlementState.PREMIUM if latest.ends_at > now else EntitlementState.EXPIRED
        ent.updated_at = now
        self.entitlements.save(ent)

    def apply_success(self, *, payment, plan, receipt, event, now) -> bool:
        current = self.payments.get(payment.id)
        if current and current.state == PaymentState.SUCCEEDED:
            self.inbox.mark_seen(event)
            return False
        payment.state = PaymentState.SUCCEEDED
        payment.updated_at = now
        wallet = self.wallets.get(payment.account_id)
        if plan.kind == "subscription":
            existing = self.grants.get_by_payment(payment.id)
            if existing is None:
                ent = self.entitlements.get(payment.account_id)
                anchor = ent.premium_until if ent.premium_until and ent.premium_until > now else now
                from datetime import timedelta
                grant = SubscriptionGrant(
                    id=f"grant-{payment.id}",
                    payment_id=payment.id,
                    account_id=payment.account_id,
                    duration_days=plan.duration_days,
                    granted_at=now,
                    starts_at=anchor,
                    ends_at=anchor + timedelta(days=plan.duration_days),
                )
                self.grants.save(grant)
            wallet.set_cycle_allowance(plan.included_ai_credits, now)
            self._recalculate_entitlement(payment.account_id, now)
        else:
            wallet.grant_purchased(plan.included_ai_credits, now)
        self.payments.save(payment)
        self.wallets.save(wallet)
        self.receipts.save(receipt)
        self.inbox.mark_seen(event)
        return True

    def apply_reversal(self, *, payment, event, now) -> bool:
        current = self.payments.get(payment.id)
        if current and current.state == PaymentState.REVERSED:
            self.inbox.mark_seen(event)
            return False
        if current and current.state != PaymentState.SUCCEEDED:
            raise ValueError("only succeeded payment can be reversed")
        payment.state = PaymentState.REVERSED
        payment.updated_at = now
        grant = self.grants.get_by_payment(payment.id)
        if grant is not None:
            grant.reverse(now)
            self.grants.save(grant)
            self._recalculate_entitlement(payment.account_id, now)
        self.payments.save(payment)
        self.inbox.mark_seen(event)
        return True

    def apply_terminal(self, *, payment, event, now) -> None:
        self.payments.save(payment)
        self.inbox.mark_seen(event)

    def consume_ai_credits(self, *, account_id: str, credits: int, now) -> int:
        wallet = self.wallets.get(account_id)
        wallet.consume(credits, now)
        self.wallets.save(wallet)
        return wallet.balance

    def reserve_ai_credits(self, *, account_id: str, credits: int, now, ttl_seconds: int = 120):
        from datetime import timedelta
        from uuid import uuid4
        wallet = self.wallets.get(account_id)
        if wallet.balance < credits:
            raise ValueError("insufficient_ai_credits")
        included = min(wallet.included_balance, credits)
        purchased = credits - included
        wallet.included_balance -= included
        wallet.purchased_balance -= purchased
        wallet.updated_at = now
        self.wallets.save(wallet)
        r = AiCreditReservation(id=str(uuid4()),account_id=account_id,credits=credits,included_credits=included,purchased_credits=purchased,state=AiReservationState.RESERVED,created_at=now,expires_at=now+timedelta(seconds=ttl_seconds),updated_at=now)
        self.ai_reservations[r.id] = r
        return r

    def commit_ai_reservation(self, *, reservation_id: str, now) -> int:
        r = self.ai_reservations.get(reservation_id)
        if not r or r.state != AiReservationState.RESERVED:
            raise ValueError("invalid_ai_reservation")
        r.state = AiReservationState.COMMITTED; r.updated_at = now
        wallet = self.wallets.get(r.account_id)
        wallet.lifetime_spent += r.credits; wallet.updated_at = now
        self.wallets.save(wallet)
        return wallet.balance

    def release_ai_reservation(self, *, reservation_id: str, now) -> int:
        r = self.ai_reservations.get(reservation_id)
        if not r or r.state != AiReservationState.RESERVED:
            raise ValueError("invalid_ai_reservation")
        r.state = AiReservationState.RELEASED; r.updated_at = now
        wallet = self.wallets.get(r.account_id)
        wallet.included_balance += r.included_credits
        wallet.purchased_balance += r.purchased_credits
        wallet.updated_at = now
        self.wallets.save(wallet)
        return wallet.balance
