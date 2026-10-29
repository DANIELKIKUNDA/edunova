from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256


class PaymentState(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"
    REVERSED = "reversed"


class EntitlementState(StrEnum):
    FREE = "free"
    PREMIUM = "premium"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "CDF"

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be > 0")
        if self.currency != "CDF":
            raise ValueError("EduNova pilot only accepts CDF")


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    price: Money
    kind: str = "subscription"
    duration_days: int = 30
    included_ai_credits: int = 25
    max_personal_documents: int = 100
    offline_enabled: bool = True

    def __post_init__(self) -> None:
        if self.kind not in {"subscription", "ai_pack"}:
            raise ValueError("unsupported product kind")
        if self.kind == "subscription" and self.duration_days < 1:
            raise ValueError("subscription duration_days must be >= 1")
        if self.kind == "ai_pack" and self.duration_days != 0:
            raise ValueError("ai_pack duration_days must be 0")
        if self.included_ai_credits < 0:
            raise ValueError("included_ai_credits must be >= 0")


@dataclass
class PaymentIntent:
    id: str
    account_id: str
    plan_code: str
    amount: Money
    phone_number: str
    idempotency_key: str
    state: PaymentState
    provider: str
    provider_reference: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    failure_reason: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def mark_pending(self, provider_reference: str, now: datetime) -> None:
        if self.state not in {PaymentState.CREATED, PaymentState.PENDING}:
            return
        self.provider_reference = provider_reference
        self.state = PaymentState.PENDING
        self.updated_at = now

    def mark_succeeded(self, now: datetime) -> bool:
        if self.state == PaymentState.SUCCEEDED:
            return False
        if self.state in {PaymentState.REVERSED, PaymentState.CANCELED}:
            raise ValueError("terminal payment cannot succeed")
        self.state = PaymentState.SUCCEEDED
        self.updated_at = now
        return True

    def mark_failed(self, reason: str, now: datetime) -> None:
        if self.state == PaymentState.SUCCEEDED:
            return
        self.state = PaymentState.FAILED
        self.failure_reason = reason
        self.updated_at = now

    def mark_reversed(self, now: datetime) -> bool:
        if self.state == PaymentState.REVERSED:
            return False
        if self.state != PaymentState.SUCCEEDED:
            raise ValueError("only succeeded payment can be reversed")
        self.state = PaymentState.REVERSED
        self.updated_at = now
        return True

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at and self.state in {PaymentState.CREATED, PaymentState.PENDING}


@dataclass
class Entitlement:
    account_id: str
    premium_until: datetime | None = None
    state: EntitlementState = EntitlementState.FREE
    source_payment_id: str | None = None
    updated_at: datetime | None = None

    def is_premium(self, now: datetime) -> bool:
        return (
            self.state == EntitlementState.PREMIUM
            and self.premium_until is not None
            and self.premium_until > now
        )

    def activate(self, *, payment_id: str, duration_days: int, now: datetime) -> None:
        anchor = now
        if self.premium_until and self.premium_until > now:
            anchor = self.premium_until
        self.premium_until = anchor + timedelta(days=duration_days)
        self.state = EntitlementState.PREMIUM
        self.source_payment_id = payment_id
        self.updated_at = now

    def reverse_if_source(self, *, payment_id: str, now: datetime) -> bool:
        if self.source_payment_id != payment_id:
            return False
        self.state = EntitlementState.SUSPENDED
        self.updated_at = now
        return True


@dataclass
class AiWallet:
    account_id: str
    included_balance: int = 0
    purchased_balance: int = 0
    lifetime_granted: int = 0
    lifetime_spent: int = 0
    updated_at: datetime | None = None

    @property
    def balance(self) -> int:
        return self.included_balance + self.purchased_balance

    def set_cycle_allowance(self, credits: int, now: datetime) -> None:
        if credits < 0:
            raise ValueError("credits must be >= 0")
        self.included_balance = credits
        self.lifetime_granted += credits
        self.updated_at = now

    def grant_purchased(self, credits: int, now: datetime) -> None:
        if credits <= 0:
            raise ValueError("credits must be > 0")
        self.purchased_balance += credits
        self.lifetime_granted += credits
        self.updated_at = now

    def consume(self, credits: int, now: datetime) -> None:
        if credits <= 0:
            raise ValueError("credits must be > 0")
        if self.balance < credits:
            raise ValueError("insufficient_ai_credits")
        from_included = min(self.included_balance, credits)
        self.included_balance -= from_included
        remaining = credits - from_included
        self.purchased_balance -= remaining
        self.lifetime_spent += credits
        self.updated_at = now


@dataclass(frozen=True)
class WebhookEvent:
    provider: str
    event_id: str
    provider_reference: str
    state: PaymentState
    amount: Money
    received_at: datetime

    @property
    def dedupe_key(self) -> str:
        raw = f"{self.provider}:{self.event_id}".encode()
        return sha256(raw).hexdigest()


@dataclass(frozen=True)
class Receipt:
    id: str
    payment_id: str
    account_id: str
    amount: Money
    issued_at: datetime
    description: str


@dataclass(frozen=True)
class EntitlementSnapshot:
    account_id: str
    premium: bool
    premium_until: datetime | None
    ai_credits_remaining: int
    issued_at: datetime
    valid_until: datetime
    revision: str

    @classmethod
    def from_state(
        cls,
        *,
        entitlement: Entitlement,
        wallet: AiWallet,
        now: datetime,
        offline_lease_hours: int = 72,
    ) -> "EntitlementSnapshot":
        premium = entitlement.is_premium(now)
        hard_expiry = entitlement.premium_until if premium else now
        lease = now + timedelta(hours=offline_lease_hours)
        valid_until = min(hard_expiry, lease) if hard_expiry else lease
        revision = sha256(
            f"{entitlement.account_id}:{entitlement.premium_until}:{wallet.balance}:{entitlement.updated_at}".encode()
        ).hexdigest()[:20]
        return cls(
            account_id=entitlement.account_id,
            premium=premium,
            premium_until=entitlement.premium_until,
            ai_credits_remaining=wallet.balance,
            issued_at=now,
            valid_until=valid_until,
            revision=revision,
        )


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class SubscriptionGrant:
    """One paid subscription right, reversible independently from later renewals."""

    id: str
    payment_id: str
    account_id: str
    duration_days: int
    granted_at: datetime
    starts_at: datetime
    ends_at: datetime
    reversed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.duration_days <= 0:
            raise ValueError("duration_days must be > 0")
        if self.ends_at <= self.starts_at:
            raise ValueError("grant end must be after start")

    @property
    def active(self) -> bool:
        return self.reversed_at is None

    def reverse(self, now: datetime) -> bool:
        if self.reversed_at is not None:
            return False
        self.reversed_at = now
        return True


class AiReservationState(StrEnum):
    RESERVED = "reserved"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass
class AiCreditReservation:
    id: str
    account_id: str
    credits: int
    included_credits: int
    purchased_credits: int
    state: AiReservationState
    created_at: datetime
    expires_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.credits <= 0 or self.included_credits < 0 or self.purchased_credits < 0:
            raise ValueError("invalid_ai_reservation")
        if self.included_credits + self.purchased_credits != self.credits:
            raise ValueError("reservation_split_mismatch")
