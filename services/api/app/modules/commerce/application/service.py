from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from app.modules.commerce.application.ports import (
    ProviderPaymentStart,
    AiWalletRepository,
    CommerceSettlement,
    EntitlementRepository,
    MobileMoneyProvider,
    PaymentRepository,
    PlanCatalog,
    ReceiptRepository,
    WebhookInbox,
)
from app.modules.commerce.domain.model import (
    EntitlementSnapshot,
    Money,
    PaymentIntent,
    PaymentState,
    Receipt,
    WebhookEvent,
)


@dataclass(frozen=True)
class CheckoutResult:
    payment: PaymentIntent
    action_type: str
    action_value: str | None
    user_message: str


class CommerceService:
    def __init__(
        self,
        *,
        payments: PaymentRepository,
        entitlements: EntitlementRepository,
        wallets: AiWalletRepository,
        receipts: ReceiptRepository,
        inbox: WebhookInbox,
        catalog: PlanCatalog,
        providers: dict[str, MobileMoneyProvider],
        settlement: CommerceSettlement,
        now: callable,
    ) -> None:
        self.payments = payments
        self.entitlements = entitlements
        self.wallets = wallets
        self.receipts = receipts
        self.inbox = inbox
        self.catalog = catalog
        self.providers = providers
        self.settlement = settlement
        self.now = now

    def create_checkout(
        self,
        *,
        account_id: str,
        plan_code: str,
        phone_number: str,
        idempotency_key: str,
        provider_name: str,
    ) -> CheckoutResult:
        existing = self.payments.get_by_idempotency(account_id, idempotency_key)
        if existing:
            requested_phone = phone_number.strip()
            if existing.plan_code != plan_code or existing.provider != provider_name or existing.phone_number != requested_phone:
                raise ValueError("idempotency_key_conflict")
            return CheckoutResult(existing, existing.metadata.get("action_type", "prompt"), existing.metadata.get("action_value"), existing.metadata.get("user_message", ""))

        plan = self.catalog.get(plan_code)
        if not plan:
            raise ValueError("unknown_plan")
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError("unsupported_payment_provider")
        if not phone_number.strip():
            raise ValueError("phone_number_required")

        now = self.now()
        payment = PaymentIntent(
            id=str(uuid4()),
            account_id=account_id,
            plan_code=plan.code,
            amount=plan.price,
            phone_number=phone_number,
            idempotency_key=idempotency_key,
            state=PaymentState.CREATED,
            provider=provider.name,
            provider_reference=None,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=15),
        )
        start = provider.create_payment(payment)
        payment.mark_pending(start.provider_reference, now)
        payment.metadata["action_type"] = start.action_type
        if start.action_value is not None:
            payment.metadata["action_value"] = start.action_value
        payment.metadata["user_message"] = start.user_message
        self.payments.save(payment)
        return CheckoutResult(payment, start.action_type, start.action_value, start.user_message)

    def process_webhook(self, *, provider_name: str, event: WebhookEvent) -> PaymentIntent:
        if event.provider != provider_name:
            raise ValueError("provider_mismatch")
        if self.inbox.has_seen(event.dedupe_key):
            payment = self.payments.get_by_provider_reference(event.provider, event.provider_reference)
            if not payment:
                raise ValueError("unknown_payment_reference")
            return payment

        payment = self.payments.get_by_provider_reference(event.provider, event.provider_reference)
        if not payment:
            raise ValueError("unknown_payment_reference")
        if payment.amount != event.amount:
            raise ValueError("payment_amount_mismatch")

        now = self.now()
        if event.state == PaymentState.SUCCEEDED:
            plan = self.catalog.get(payment.plan_code)
            if not plan:
                raise ValueError("unknown_plan")
            receipt = Receipt(
                id=str(uuid4()),
                payment_id=payment.id,
                account_id=payment.account_id,
                amount=payment.amount,
                issued_at=now,
                description=(f"EduNova {plan.name} — {plan.duration_days} jours" if plan.kind == "subscription" else f"EduNova {plan.name} — {plan.included_ai_credits} crédits IA"),
            )
            self.settlement.apply_success(payment=payment, plan=plan, receipt=receipt, event=event, now=now)
        elif event.state == PaymentState.REVERSED:
            self.settlement.apply_reversal(payment=payment, event=event, now=now)
        elif event.state == PaymentState.FAILED:
            payment.mark_failed("provider_failed", now)
            self.settlement.apply_terminal(payment=payment, event=event, now=now)
        elif event.state == PaymentState.CANCELED:
            payment.state = PaymentState.CANCELED
            payment.updated_at = now
            self.settlement.apply_terminal(payment=payment, event=event, now=now)
        elif event.state == PaymentState.EXPIRED:
            payment.state = PaymentState.EXPIRED
            payment.updated_at = now
            self.settlement.apply_terminal(payment=payment, event=event, now=now)
        return self.payments.get(payment.id) or payment


    def consume_ai_credits(self, *, account_id: str, credits: int) -> int:
        return self.settlement.consume_ai_credits(account_id=account_id, credits=credits, now=self.now())

    def reserve_ai_credits(self, *, account_id: str, credits: int):
        return self.settlement.reserve_ai_credits(account_id=account_id, credits=credits, now=self.now())

    def commit_ai_reservation(self, reservation_id: str) -> int:
        return self.settlement.commit_ai_reservation(reservation_id=reservation_id, now=self.now())

    def release_ai_reservation(self, reservation_id: str) -> int:
        return self.settlement.release_ai_reservation(reservation_id=reservation_id, now=self.now())

    def expire_stale_checkouts(self, *, limit: int = 100) -> int:
        now = self.now()
        expired = self.payments.list_open_expired(now, limit)
        for payment in expired:
            payment.state = PaymentState.EXPIRED
            payment.updated_at = now
            payment.failure_reason = "checkout_expired"
            self.payments.save(payment)
        return len(expired)

    def snapshot(self, account_id: str) -> EntitlementSnapshot:
        now = self.now()
        return EntitlementSnapshot.from_state(
            entitlement=self.entitlements.get(account_id),
            wallet=self.wallets.get(account_id),
            now=now,
        )
