"""Campus paid checkout: verified provider event -> atomic, single licence grant.

A provider reference alone is never evidence of payment. No direct paid
provisioning method is exposed to HTTP callers.
"""
from __future__ import annotations

from datetime import timedelta, timezone
from uuid import uuid4
from sqlalchemy import DateTime, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.commerce.domain.model import PaymentIntent, PaymentState, Money
from app.modules.commerce.infrastructure.sqlalchemy_repo import PaymentIntentRow
from app.modules.commerce.infrastructure.sqlalchemy_repo import CampusLicenseRow


class CampusPaidOrderRow(Base):
    __tablename__ = 'campus_paid_orders'
    __table_args__ = (UniqueConstraint('institution_id', 'idempotency_key', name='uq_campus_paid_order_idempotency'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64))
    offer_code: Mapped[str] = mapped_column(String(64))
    offer_revision: Mapped[int] = mapped_column(Integer)
    amount_cdf: Mapped[int] = mapped_column(Integer)
    seats: Mapped[int] = mapped_column(Integer)
    duration_days: Mapped[int] = mapped_column(Integer)
    grace_days: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    payment_id: Mapped[str] = mapped_column(String(64), unique=True)
    license_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))


class CampusPaidCheckoutService:
    def __init__(self, sessions, commercial, providers, now):
        self.sessions, self.commercial, self.providers, self.now = sessions, commercial, providers, now

    def checkout(self, *, institution_id, actor_id, offer_code, phone_number, provider_name, idempotency_key):
        from app.modules.commerce.application.campus_offers import CampusOfferRow
        self.commercial._admin(institution_id, actor_id)
        if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 128 or idempotency_key != idempotency_key.strip():
            raise ValueError('invalid_idempotency_key')
        if not isinstance(phone_number, str) or not 6 <= len(phone_number.strip()) <= 32:
            raise ValueError('invalid_phone_number')
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError('unsupported_payment_provider')
        with self.sessions.begin() as s:
            existing = s.scalar(select(CampusPaidOrderRow).where(CampusPaidOrderRow.institution_id == institution_id, CampusPaidOrderRow.idempotency_key == idempotency_key))
            if existing:
                payment = s.get(PaymentIntentRow, existing.payment_id)
                if (existing.account_id != actor_id or existing.offer_code != offer_code or payment.provider != provider_name or payment.phone_number != phone_number.strip()):
                    raise ValueError('idempotency_key_conflict')
                return self._response(existing, payment)
            offer = s.get(CampusOfferRow, offer_code)
            if not offer or not offer.active or offer.price_cdf <= 0:
                raise ValueError('paid_campus_offer_unavailable')
            now = self.now()
            payment = PaymentIntent(str(uuid4()), actor_id, 'campus:'+offer.code, Money(offer.price_cdf), phone_number.strip(), 'campus:'+institution_id+':'+idempotency_key, PaymentState.CREATED, provider_name, None, now, now, now+timedelta(minutes=15))
            started = provider.create_payment(payment)
            payment.mark_pending(started.provider_reference, now)
            s.add(PaymentIntentRow(id=payment.id, account_id=actor_id, plan_code=payment.plan_code, amount_cdf=offer.price_cdf, phone_number=payment.phone_number, idempotency_key=payment.idempotency_key, state=payment.state.value, provider=provider_name, provider_reference=payment.provider_reference, created_at=now, updated_at=now, expires_at=payment.expires_at, metadata_json='{}'))
            order = CampusPaidOrderRow(id=str(uuid4()), institution_id=institution_id, account_id=actor_id, offer_code=offer.code, offer_revision=offer.revision, amount_cdf=offer.price_cdf, seats=offer.seats, duration_days=offer.duration_days, grace_days=offer.grace_days, idempotency_key=idempotency_key, payment_id=payment.id, license_id=None, status='pending', created_at=now)
            s.add(order)
            return self._response(order, s.get(PaymentIntentRow, payment.id) or payment, started)

    @staticmethod
    def _response(order, payment, started=None):
        return {'order_id': order.id, 'institution_id': order.institution_id, 'offer_code': order.offer_code, 'amount_cdf': order.amount_cdf, 'payment_id': order.payment_id, 'state': order.status, 'provider_reference': payment.provider_reference, 'action_type': started.action_type if started else 'prompt', 'action_value': started.action_value if started else None}

    def is_campus_payment(self, provider_name, provider_reference):
        with self.sessions() as s:
            payment = s.scalar(select(PaymentIntentRow).where(PaymentIntentRow.provider == provider_name, PaymentIntentRow.provider_reference == provider_reference))
            return bool(payment and payment.plan_code.startswith('campus:'))

    def verified_event(self, *, provider_name, event):
        """Call only after verifying the provider's webhook signature."""
        if event.provider != provider_name:
            raise ValueError('provider_mismatch')
        with self.sessions.begin() as s:
            payment = s.scalar(select(PaymentIntentRow).where(PaymentIntentRow.provider == provider_name, PaymentIntentRow.provider_reference == event.provider_reference).with_for_update())
            if not payment or not payment.plan_code.startswith('campus:'):
                raise ValueError('unknown_campus_payment')
            order = s.scalar(select(CampusPaidOrderRow).where(CampusPaidOrderRow.payment_id == payment.id).with_for_update())
            if not order or order.amount_cdf != event.amount.amount or event.amount.currency != 'CDF' or payment.amount_cdf != order.amount_cdf:
                raise ValueError('campus_payment_amount_mismatch')
            if order.status == 'succeeded':
                return {'accepted': True, 'payment_id': payment.id, 'state': 'succeeded', 'license_id': order.license_id, 'duplicate': True}
            if order.status != 'pending' or payment.state not in ('pending', 'created'):
                return {'accepted': True, 'payment_id': payment.id, 'state': order.status, 'license_id': None, 'duplicate': True}
            now = self.now()
            if event.state == PaymentState.SUCCEEDED:
                previous = s.scalar(select(CampusLicenseRow).where(CampusLicenseRow.institution_id == order.institution_id).order_by(CampusLicenseRow.ends_at.desc()).with_for_update())
                if previous and previous.state in ('suspended', 'canceled'):
                    # Preserve confirmed funds for manual resolution, never silently reinstate.
                    order.status = 'paid_review'; payment.state = 'succeeded'
                else:
                    start = max(now, previous.ends_at.replace(tzinfo=timezone.utc) if previous and previous.ends_at.tzinfo is None else previous.ends_at) if previous else now
                    end = start + timedelta(days=order.duration_days)
                    lic = CampusLicenseRow(id=str(uuid4()), institution_id=order.institution_id, plan_code=order.offer_code, state='active', seats=order.seats, price_cdf=order.amount_cdf, starts_at=start, ends_at=end, grace_until=end+timedelta(days=order.grace_days), created_by=order.account_id, created_at=now)
                    s.add(lic); order.license_id=lic.id; order.status='succeeded'; payment.state='succeeded'
            elif event.state in (PaymentState.FAILED, PaymentState.CANCELED, PaymentState.EXPIRED):
                order.status=event.state.value; payment.state=event.state.value
            elif event.state == PaymentState.REVERSED:
                order.status='paid_review'; payment.state='reversed'
            payment.updated_at=now
            return {'accepted': True, 'payment_id': payment.id, 'state': order.status, 'license_id': order.license_id, 'duplicate': False}

    def status(self, *, institution_id, actor_id, order_id):
        self.commercial._admin(institution_id, actor_id)
        with self.sessions() as s:
            order=s.get(CampusPaidOrderRow, order_id)
            if not order or order.institution_id != institution_id:
                raise ValueError('campus_order_not_found')
            return {'order_id':order.id,'status':order.status,'payment_id':order.payment_id,'license_id':order.license_id,'amount_cdf':order.amount_cdf}
