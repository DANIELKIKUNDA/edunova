from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.commerce.domain.model import (
    AiWallet,
    AiCreditReservation,
    AiReservationState,
    Entitlement,
    EntitlementState,
    Money,
    PaymentIntent,
    PaymentState,
    Receipt,
    SubscriptionGrant,
    WebhookEvent,
)
from app.shared.infrastructure.database import Base


class PaymentIntentRow(Base):
    __tablename__ = "payment_intents"
    __table_args__ = (UniqueConstraint("account_id", "idempotency_key", name="uq_payment_account_idempotency"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    plan_code: Mapped[str] = mapped_column(String(64))
    amount_cdf: Mapped[int] = mapped_column(Integer)
    phone_number: Mapped[str] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(160), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class EntitlementRow(Base):
    __tablename__ = "entitlements"
    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="free")
    source_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SubscriptionGrantRow(Base):
    __tablename__ = "subscription_grants"
    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    duration_days: Mapped[int] = mapped_column(Integer)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiWalletRow(Base):
    __tablename__ = "ai_wallets"
    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    included_balance: Mapped[int] = mapped_column(Integer, default=0)
    purchased_balance: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_granted: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_spent: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiCreditReservationRow(Base):
    __tablename__ = "ai_credit_reservations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    credits: Mapped[int] = mapped_column(Integer)
    included_credits: Mapped[int] = mapped_column(Integer)
    purchased_credits: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReceiptRow(Base):
    __tablename__ = "receipts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_cdf: Mapped[int] = mapped_column(Integer)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(String(255))


class WebhookInboxRow(Base):
    __tablename__ = "webhook_inbox"
    dedupe_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(160))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyPaymentRepository:
    def __init__(self, session_factory) -> None: self.session_factory = session_factory
    def get(self, payment_id: str):
        with self.session_factory() as s:
            row = s.get(PaymentIntentRow, payment_id); return _payment(row) if row else None
    def get_by_idempotency(self, account_id: str, key: str):
        with self.session_factory() as s:
            row = s.scalar(select(PaymentIntentRow).where(PaymentIntentRow.account_id==account_id, PaymentIntentRow.idempotency_key==key)); return _payment(row) if row else None
    def get_by_provider_reference(self, provider: str, reference: str):
        with self.session_factory() as s:
            row = s.scalar(select(PaymentIntentRow).where(PaymentIntentRow.provider==provider, PaymentIntentRow.provider_reference==reference)); return _payment(row) if row else None
    def list_open_expired(self, now, limit: int = 100) -> list[PaymentIntent]:
        with self.session_factory() as s:
            rows = s.scalars(select(PaymentIntentRow).where(
                PaymentIntentRow.state.in_([PaymentState.CREATED.value, PaymentState.PENDING.value]),
                PaymentIntentRow.expires_at <= now,
            ).limit(limit)).all()
            return [_payment(r) for r in rows]
    def save(self, p: PaymentIntent) -> None:
        with self.session_factory() as s:
            s.merge(PaymentIntentRow(id=p.id, account_id=p.account_id, plan_code=p.plan_code, amount_cdf=p.amount.amount, phone_number=p.phone_number, idempotency_key=p.idempotency_key, state=p.state.value, provider=p.provider, provider_reference=p.provider_reference, created_at=p.created_at, updated_at=p.updated_at, expires_at=p.expires_at, failure_reason=p.failure_reason, metadata_json=json.dumps(p.metadata))); s.commit()


class SqlAlchemyEntitlementRepository:
    def __init__(self, session_factory) -> None: self.session_factory = session_factory
    def get(self, account_id: str) -> Entitlement:
        with self.session_factory() as s:
            row=s.get(EntitlementRow, account_id)
            return Entitlement(account_id=account_id) if not row else Entitlement(account_id=row.account_id,premium_until=_utc(row.premium_until),state=EntitlementState(row.state),source_payment_id=row.source_payment_id,updated_at=_utc(row.updated_at))
    def save(self, e: Entitlement) -> None:
        with self.session_factory() as s:
            s.merge(EntitlementRow(account_id=e.account_id,premium_until=e.premium_until,state=e.state.value,source_payment_id=e.source_payment_id,updated_at=e.updated_at)); s.commit()


class SqlAlchemyAiWalletRepository:
    def __init__(self, session_factory) -> None: self.session_factory=session_factory
    def get(self, account_id: str) -> AiWallet:
        with self.session_factory() as s:
            row=s.get(AiWalletRow, account_id)
            return AiWallet(account_id=account_id) if not row else AiWallet(account_id=row.account_id,included_balance=row.included_balance,purchased_balance=row.purchased_balance,lifetime_granted=row.lifetime_granted,lifetime_spent=row.lifetime_spent,updated_at=_utc(row.updated_at))
    def save(self, w: AiWallet) -> None:
        with self.session_factory() as s:
            s.merge(AiWalletRow(account_id=w.account_id,included_balance=w.included_balance,purchased_balance=w.purchased_balance,lifetime_granted=w.lifetime_granted,lifetime_spent=w.lifetime_spent,updated_at=w.updated_at)); s.commit()


class SqlAlchemySubscriptionGrantRepository:
    def __init__(self, session_factory) -> None: self.session_factory = session_factory

    def get_by_payment(self, payment_id: str) -> SubscriptionGrant | None:
        with self.session_factory() as s:
            row = s.scalar(select(SubscriptionGrantRow).where(SubscriptionGrantRow.payment_id == payment_id))
            return _grant(row) if row else None

    def list_for_account(self, account_id: str) -> list[SubscriptionGrant]:
        with self.session_factory() as s:
            rows = s.scalars(select(SubscriptionGrantRow).where(SubscriptionGrantRow.account_id == account_id).order_by(SubscriptionGrantRow.granted_at.asc())).all()
            return [_grant(r) for r in rows]

    def save(self, g: SubscriptionGrant) -> None:
        with self.session_factory() as s:
            s.merge(SubscriptionGrantRow(id=g.id,payment_id=g.payment_id,account_id=g.account_id,duration_days=g.duration_days,granted_at=g.granted_at,starts_at=g.starts_at,ends_at=g.ends_at,reversed_at=g.reversed_at))
            s.commit()


class SqlAlchemyReceiptRepository:
    def __init__(self, session_factory) -> None: self.session_factory=session_factory
    def save(self, r: Receipt) -> None:
        with self.session_factory() as s:
            exists=s.scalar(select(ReceiptRow).where(ReceiptRow.payment_id==r.payment_id))
            if not exists:
                s.add(ReceiptRow(id=r.id,payment_id=r.payment_id,account_id=r.account_id,amount_cdf=r.amount.amount,issued_at=_utc(r.issued_at),description=r.description)); s.commit()
    def list_for_account(self, account_id: str) -> list[Receipt]:
        with self.session_factory() as s:
            rows=s.scalars(select(ReceiptRow).where(ReceiptRow.account_id==account_id).order_by(ReceiptRow.issued_at.desc())).all()
            return [Receipt(id=r.id,payment_id=r.payment_id,account_id=r.account_id,amount=Money(r.amount_cdf),issued_at=_utc(r.issued_at),description=r.description) for r in rows]


class SqlAlchemyWebhookInbox:
    def __init__(self, session_factory) -> None: self.session_factory=session_factory
    def has_seen(self, key: str) -> bool:
        with self.session_factory() as s: return s.get(WebhookInboxRow,key) is not None
    def mark_seen(self, e: WebhookEvent) -> None:
        with self.session_factory() as s:
            if not s.get(WebhookInboxRow,e.dedupe_key): s.add(WebhookInboxRow(dedupe_key=e.dedupe_key,provider=e.provider,event_id=e.event_id,received_at=e.received_at)); s.commit()



def _utc(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _payment(r: PaymentIntentRow) -> PaymentIntent:
    return PaymentIntent(id=r.id,account_id=r.account_id,plan_code=r.plan_code,amount=Money(r.amount_cdf),phone_number=r.phone_number,idempotency_key=r.idempotency_key,state=PaymentState(r.state),provider=r.provider,provider_reference=r.provider_reference,created_at=_utc(r.created_at),updated_at=_utc(r.updated_at),expires_at=_utc(r.expires_at),failure_reason=r.failure_reason,metadata=json.loads(r.metadata_json or "{}"))

def _grant(r: SubscriptionGrantRow) -> SubscriptionGrant:
    return SubscriptionGrant(id=r.id,payment_id=r.payment_id,account_id=r.account_id,duration_days=r.duration_days,granted_at=_utc(r.granted_at),starts_at=_utc(r.starts_at),ends_at=_utc(r.ends_at),reversed_at=_utc(r.reversed_at))


class SqlAlchemyCommerceSettlement:
    """Atomic payment settlement with reversible subscription-grant ledger."""
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _recalculate_entitlement(session, account_id: str, now) -> None:
        ent = session.get(EntitlementRow, account_id)
        if ent is None:
            ent = EntitlementRow(account_id=account_id,premium_until=None,state=EntitlementState.FREE.value,source_payment_id=None,updated_at=now)
            session.add(ent)
        active = session.scalars(
            select(SubscriptionGrantRow)
            .where(SubscriptionGrantRow.account_id == account_id, SubscriptionGrantRow.reversed_at.is_(None))
            .order_by(SubscriptionGrantRow.ends_at.desc())
        ).all()
        if not active:
            ent.premium_until = None
            ent.state = EntitlementState.FREE.value
            ent.source_payment_id = None
            ent.updated_at = now
            return
        latest = active[0]
        ent.premium_until = latest.ends_at
        ent.state = EntitlementState.PREMIUM.value if _utc(latest.ends_at) > now else EntitlementState.EXPIRED.value
        ent.source_payment_id = latest.payment_id
        ent.updated_at = now

    def apply_success(self, *, payment: PaymentIntent, plan, receipt: Receipt, event: WebhookEvent, now) -> bool:
        from datetime import timedelta
        with self.session_factory.begin() as session:
            row = session.scalar(select(PaymentIntentRow).where(PaymentIntentRow.id == payment.id).with_for_update())
            if row is None:
                raise ValueError("unknown_payment_reference")
            if row.state == PaymentState.SUCCEEDED.value:
                self._mark_event(session, event)
                return False
            if row.state == PaymentState.REVERSED.value:
                raise ValueError("reversed_payment_cannot_succeed")
            row.state = PaymentState.SUCCEEDED.value
            row.updated_at = now

            wallet = session.get(AiWalletRow, payment.account_id)
            if wallet is None:
                wallet = AiWalletRow(account_id=payment.account_id,included_balance=0,purchased_balance=0,lifetime_granted=0,lifetime_spent=0,updated_at=None)
                session.add(wallet)

            if plan.kind == "subscription":
                existing_grant = session.scalar(select(SubscriptionGrantRow).where(SubscriptionGrantRow.payment_id == payment.id))
                if existing_grant is None:
                    ent = session.get(EntitlementRow, payment.account_id)
                    current_until = _utc(ent.premium_until) if ent else None
                    anchor = current_until if current_until and current_until > now else now
                    grant = SubscriptionGrantRow(
                        id=f"grant-{payment.id}", payment_id=payment.id, account_id=payment.account_id,
                        duration_days=plan.duration_days, granted_at=now, starts_at=anchor,
                        ends_at=anchor + timedelta(days=plan.duration_days), reversed_at=None,
                    )
                    session.add(grant)
                wallet.included_balance = plan.included_ai_credits
                wallet.lifetime_granted += plan.included_ai_credits
                wallet.updated_at = now
                session.flush()
                self._recalculate_entitlement(session, payment.account_id, now)
            else:
                wallet.purchased_balance += plan.included_ai_credits
                wallet.lifetime_granted += plan.included_ai_credits
                wallet.updated_at = now

            existing_receipt = session.scalar(select(ReceiptRow).where(ReceiptRow.payment_id == receipt.payment_id))
            if existing_receipt is None:
                session.add(ReceiptRow(id=receipt.id,payment_id=receipt.payment_id,account_id=receipt.account_id,amount_cdf=receipt.amount.amount,issued_at=receipt.issued_at,description=receipt.description))
            self._mark_event(session, event)
            return True

    def apply_reversal(self, *, payment: PaymentIntent, event: WebhookEvent, now) -> bool:
        with self.session_factory.begin() as session:
            row = session.scalar(select(PaymentIntentRow).where(PaymentIntentRow.id == payment.id).with_for_update())
            if row is None:
                raise ValueError("unknown_payment_reference")
            if row.state == PaymentState.REVERSED.value:
                self._mark_event(session, event)
                return False
            if row.state != PaymentState.SUCCEEDED.value:
                raise ValueError("only succeeded payment can be reversed")
            row.state = PaymentState.REVERSED.value
            row.updated_at = now
            grant = session.scalar(select(SubscriptionGrantRow).where(SubscriptionGrantRow.payment_id == payment.id).with_for_update())
            if grant is not None and grant.reversed_at is None:
                grant.reversed_at = now
                session.flush()
                self._recalculate_entitlement(session, payment.account_id, now)
            self._mark_event(session, event)
            return True

    def apply_terminal(self, *, payment: PaymentIntent, event: WebhookEvent, now) -> None:
        with self.session_factory.begin() as session:
            row = session.scalar(select(PaymentIntentRow).where(PaymentIntentRow.id == payment.id).with_for_update())
            if row is None:
                raise ValueError("unknown_payment_reference")
            # A late FAILED/CANCELED/EXPIRED event must never downgrade a settled payment.
            if row.state not in {PaymentState.SUCCEEDED.value, PaymentState.REVERSED.value}:
                row.state = payment.state.value
                row.updated_at = now
                row.failure_reason = payment.failure_reason
            self._mark_event(session, event)

    def consume_ai_credits(self, *, account_id: str, credits: int, now) -> int:
        if credits <= 0:
            raise ValueError("credits must be > 0")
        with self.session_factory.begin() as session:
            wallet = session.scalar(select(AiWalletRow).where(AiWalletRow.account_id == account_id).with_for_update())
            if wallet is None:
                raise ValueError("insufficient_ai_credits")
            balance = wallet.included_balance + wallet.purchased_balance
            if balance < credits:
                raise ValueError("insufficient_ai_credits")
            from_included = min(wallet.included_balance, credits)
            wallet.included_balance -= from_included
            wallet.purchased_balance -= (credits - from_included)
            wallet.lifetime_spent += credits
            wallet.updated_at = now
            return wallet.included_balance + wallet.purchased_balance

    def reserve_ai_credits(self, *, account_id: str, credits: int, now, ttl_seconds: int = 120):
        from datetime import timedelta
        from uuid import uuid4
        if credits <= 0:
            raise ValueError("credits must be > 0")
        with self.session_factory.begin() as session:
            wallet = session.scalar(select(AiWalletRow).where(AiWalletRow.account_id == account_id).with_for_update())
            if wallet is None or wallet.included_balance + wallet.purchased_balance < credits:
                raise ValueError("insufficient_ai_credits")
            included = min(wallet.included_balance, credits)
            purchased = credits - included
            wallet.included_balance -= included
            wallet.purchased_balance -= purchased
            wallet.updated_at = now
            rid = str(uuid4())
            session.add(AiCreditReservationRow(id=rid,account_id=account_id,credits=credits,included_credits=included,purchased_credits=purchased,state=AiReservationState.RESERVED.value,created_at=now,expires_at=now+timedelta(seconds=ttl_seconds),updated_at=now))
            return AiCreditReservation(id=rid,account_id=account_id,credits=credits,included_credits=included,purchased_credits=purchased,state=AiReservationState.RESERVED,created_at=now,expires_at=now+timedelta(seconds=ttl_seconds),updated_at=now)

    def commit_ai_reservation(self, *, reservation_id: str, now) -> int:
        with self.session_factory.begin() as session:
            r = session.scalar(select(AiCreditReservationRow).where(AiCreditReservationRow.id == reservation_id).with_for_update())
            if r is None or r.state != AiReservationState.RESERVED.value:
                raise ValueError("invalid_ai_reservation")
            wallet = session.scalar(select(AiWalletRow).where(AiWalletRow.account_id == r.account_id).with_for_update())
            if wallet is None:
                raise ValueError("ai_wallet_missing")
            r.state = AiReservationState.COMMITTED.value; r.updated_at = now
            wallet.lifetime_spent += r.credits; wallet.updated_at = now
            return wallet.included_balance + wallet.purchased_balance

    def release_ai_reservation(self, *, reservation_id: str, now) -> int:
        with self.session_factory.begin() as session:
            r = session.scalar(select(AiCreditReservationRow).where(AiCreditReservationRow.id == reservation_id).with_for_update())
            if r is None or r.state != AiReservationState.RESERVED.value:
                raise ValueError("invalid_ai_reservation")
            wallet = session.scalar(select(AiWalletRow).where(AiWalletRow.account_id == r.account_id).with_for_update())
            if wallet is None:
                raise ValueError("ai_wallet_missing")
            wallet.included_balance += r.included_credits
            wallet.purchased_balance += r.purchased_credits
            wallet.updated_at = now
            r.state = AiReservationState.RELEASED.value; r.updated_at = now
            return wallet.included_balance + wallet.purchased_balance

    @staticmethod
    def _mark_event(session, event: WebhookEvent) -> None:
        if session.get(WebhookInboxRow, event.dedupe_key) is None:
            session.add(WebhookInboxRow(dedupe_key=event.dedupe_key,provider=event.provider,event_id=event.event_id,received_at=event.received_at))

# LOT 29 — Campus licensing, commercial ledger and partner revenue sharing.
from app.modules.commerce.domain.commercial import CampusLicense, LicenseState, CommercialLedgerEntry, LedgerKind, RevenuePartner, PartnerState, RevenueShareRule, PartnerSettlement

class CampusLicenseRow(Base):
    __tablename__='campus_licenses'
    id:Mapped[str]=mapped_column(String(64),primary_key=True); institution_id:Mapped[str]=mapped_column(String(64),index=True); plan_code:Mapped[str]=mapped_column(String(64)); state:Mapped[str]=mapped_column(String(24),index=True); seats:Mapped[int]=mapped_column(Integer); price_cdf:Mapped[int]=mapped_column(Integer); starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True)); ends_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True); grace_until:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); created_by:Mapped[str]=mapped_column(String(64)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class CommercialLedgerRow(Base):
    __tablename__='commercial_ledger'
    __table_args__=(UniqueConstraint('kind','reference_type','reference_id','partner_id',name='uq_commercial_ledger_business_event'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True); institution_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); account_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); partner_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); kind:Mapped[str]=mapped_column(String(32),index=True); reference_type:Mapped[str]=mapped_column(String(32)); reference_id:Mapped[str]=mapped_column(String(96),index=True); amount_cdf:Mapped[int]=mapped_column(Integer); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True); metadata_json:Mapped[str]=mapped_column(Text,default='{}')
class RevenuePartnerRow(Base):
    __tablename__='revenue_partners'
    id:Mapped[str]=mapped_column(String(64),primary_key=True); name:Mapped[str]=mapped_column(String(160)); share_bps:Mapped[int]=mapped_column(Integer); state:Mapped[str]=mapped_column(String(24)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class RevenueShareRuleRow(Base):
    __tablename__='revenue_share_rules'
    id:Mapped[str]=mapped_column(String(64),primary_key=True); partner_id:Mapped[str]=mapped_column(String(64),index=True); institution_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); product_code:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); share_bps:Mapped[int]=mapped_column(Integer); starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True)); ends_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class PartnerSettlementRow(Base):
    __tablename__='partner_settlements'
    __table_args__=(UniqueConstraint('partner_id','period_start','period_end',name='uq_partner_settlement_period'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True); partner_id:Mapped[str]=mapped_column(String(64),index=True); period_start:Mapped[datetime]=mapped_column(DateTime(timezone=True)); period_end:Mapped[datetime]=mapped_column(DateTime(timezone=True)); gross_cdf:Mapped[int]=mapped_column(Integer); partner_cdf:Mapped[int]=mapped_column(Integer); platform_cdf:Mapped[int]=mapped_column(Integer); status:Mapped[str]=mapped_column(String(24)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))

class SqlAlchemyCommercialRepository:
    def __init__(self,sf):self.sf=sf
    def save_license(self,x):
        with self.sf() as s:s.add(CampusLicenseRow(id=x.id,institution_id=x.institution_id,plan_code=x.plan_code,state=x.state.value,seats=x.seats,price_cdf=x.price_cdf,starts_at=x.starts_at,ends_at=x.ends_at,grace_until=x.grace_until,created_by=x.created_by,created_at=x.created_at));s.commit()
    def renew_license_atomic(self, *, institution_id, license_id, plan_code, seats, price_cdf, duration_days, grace_days, actor_id, now):
        """One transaction for licence and ledger; repeat references cannot extend twice."""
        if seats < 1 or price_cdf < 0:
            raise ValueError('invalid_campus_license')
        with self.sf() as session:
            existing = session.get(CampusLicenseRow, license_id)
            if existing:
                if (existing.institution_id != institution_id or existing.plan_code != plan_code
                    or existing.seats != seats or existing.price_cdf != price_cdf
                    or existing.ends_at - existing.starts_at != timedelta(days=duration_days)
                    or existing.grace_until - existing.ends_at != timedelta(days=grace_days)):
                    raise ValueError('renewal_reference_conflict')
                row = existing
            else:
                previous = session.scalar(select(CampusLicenseRow).where(
                    CampusLicenseRow.institution_id == institution_id
                ).order_by(CampusLicenseRow.ends_at.desc()))
                # Extend the paid period, not the grace window. Never extend suspended
                # or cancelled rights without an explicit separate governance decision.
                if previous and previous.state in {'suspended', 'canceled'}:
                    raise ValueError('license_suspended_or_canceled')
                start = max(now, _utc(previous.ends_at)) if previous else now
                end = start + timedelta(days=duration_days)
                row = CampusLicenseRow(
                    id=license_id, institution_id=institution_id, plan_code=plan_code,
                    state='active', seats=seats, price_cdf=price_cdf, starts_at=start,
                    ends_at=end, grace_until=end + timedelta(days=grace_days),
                    created_by=actor_id, created_at=now,
                )
                session.add(row)
                # This is a provisioning entry, NOT a verified Mobile Money receipt.
                if price_cdf:
                    session.add(CommercialLedgerRow(
                        id=license_id, institution_id=institution_id, account_id=None,
                        partner_id=None, kind='license', reference_type='campus_renewal',
                        reference_id=license_id, amount_cdf=price_cdf,
                        created_at=now, metadata_json='{}',
                    ))
                session.commit()
            return CampusLicense(row.id, row.institution_id, row.plan_code,
                LicenseState(row.state), row.seats, row.price_cdf, _utc(row.starts_at),
                _utc(row.ends_at), _utc(row.grace_until), row.created_by, _utc(row.created_at))

    def current_license(self,i):
        with self.sf() as s:
            r=s.scalar(select(CampusLicenseRow).where(CampusLicenseRow.institution_id==i).order_by(CampusLicenseRow.ends_at.desc()))
            return None if not r else CampusLicense(r.id,r.institution_id,r.plan_code,LicenseState(r.state),r.seats,r.price_cdf,_utc(r.starts_at),_utc(r.ends_at),_utc(r.grace_until),r.created_by,_utc(r.created_at))
    def append_ledger(self,x):
        with self.sf() as s:
            existing=s.scalar(select(CommercialLedgerRow).where(CommercialLedgerRow.kind==x.kind.value,CommercialLedgerRow.reference_type==x.reference_type,CommercialLedgerRow.reference_id==x.reference_id,CommercialLedgerRow.partner_id==x.partner_id))
            if existing:return False
            s.add(CommercialLedgerRow(id=x.id,institution_id=x.institution_id,account_id=x.account_id,partner_id=x.partner_id,kind=x.kind.value,reference_type=x.reference_type,reference_id=x.reference_id,amount_cdf=x.amount_cdf,created_at=x.created_at,metadata_json=x.metadata_json));s.commit();return True
    def save_partner(self,x):
        with self.sf() as s:s.add(RevenuePartnerRow(id=x.id,name=x.name,share_bps=x.share_bps,state=x.state.value,created_at=x.created_at));s.commit()
    def save_rule(self,x):
        with self.sf() as s:s.add(RevenueShareRuleRow(id=x.id,partner_id=x.partner_id,institution_id=x.institution_id,product_code=x.product_code,share_bps=x.share_bps,starts_at=x.starts_at,ends_at=x.ends_at));s.commit()
    def active_rule(self,i,p,now):
        with self.sf() as s:
            r=s.scalar(select(RevenueShareRuleRow).where(RevenueShareRuleRow.institution_id==i,RevenueShareRuleRow.starts_at<=now,(RevenueShareRuleRow.ends_at.is_(None)| (RevenueShareRuleRow.ends_at>now)),(RevenueShareRuleRow.product_code.is_(None)|(RevenueShareRuleRow.product_code==p))).order_by(RevenueShareRuleRow.starts_at.desc()))
            return None if not r else RevenueShareRule(r.id,r.partner_id,r.institution_id,r.product_code,r.share_bps,_utc(r.starts_at),_utc(r.ends_at))
    def partner_entries(self,p,a,b):
        with self.sf() as s:
            rows=s.scalars(select(CommercialLedgerRow).where(CommercialLedgerRow.partner_id==p,CommercialLedgerRow.created_at>=a,CommercialLedgerRow.created_at<b)).all()
            return [CommercialLedgerEntry(r.id,r.institution_id,r.account_id,r.partner_id,LedgerKind(r.kind),r.reference_type,r.reference_id,r.amount_cdf,_utc(r.created_at),r.metadata_json) for r in rows]
    def save_settlement(self,x):
        with self.sf() as s:
            old=s.scalar(select(PartnerSettlementRow).where(PartnerSettlementRow.partner_id==x.partner_id,PartnerSettlementRow.period_start==x.period_start,PartnerSettlementRow.period_end==x.period_end))
            if old:return PartnerSettlement(old.id,old.partner_id,_utc(old.period_start),_utc(old.period_end),old.gross_cdf,old.partner_cdf,old.platform_cdf,old.status,_utc(old.created_at))
            s.add(PartnerSettlementRow(id=x.id,partner_id=x.partner_id,period_start=x.period_start,period_end=x.period_end,gross_cdf=x.gross_cdf,partner_cdf=x.partner_cdf,platform_cdf=x.platform_cdf,status=x.status,created_at=x.created_at));s.commit();return x
    def get_settlement(self,settlement_id):
        with self.sf() as s:
            r=s.get(PartnerSettlementRow,settlement_id)
            return None if not r else PartnerSettlement(r.id,r.partner_id,_utc(r.period_start),_utc(r.period_end),r.gross_cdf,r.partner_cdf,r.platform_cdf,r.status,_utc(r.created_at))
    def transition_settlement(self,settlement_id,from_states,to_state):
        with self.sf() as s:
            r=s.get(PartnerSettlementRow,settlement_id)
            if not r:raise ValueError('settlement_not_found')
            if r.status==to_state:return self.get_settlement(settlement_id)
            if r.status not in from_states:raise ValueError('invalid_settlement_transition')
            r.status=to_state;s.commit()
        return self.get_settlement(settlement_id)
    def update_license_state(self,license_id,state):
        with self.sf() as s:
            r=s.get(CampusLicenseRow,license_id)
            if not r:raise ValueError('license_not_found')
            r.state=state.value;s.commit()
    def ledger_has(self,kind,reference_type,reference_id,partner_id=None):
        with self.sf() as s:return s.scalar(select(CommercialLedgerRow.id).where(CommercialLedgerRow.kind==kind.value,CommercialLedgerRow.reference_type==reference_type,CommercialLedgerRow.reference_id==reference_id,CommercialLedgerRow.partner_id==partner_id)) is not None
