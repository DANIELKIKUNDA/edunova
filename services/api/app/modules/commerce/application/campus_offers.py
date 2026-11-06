"""Versioned institutional offer catalogue. A quote is not proof of payment."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base

class CampusOfferRow(Base):
    __tablename__ = 'campus_commercial_offers'
    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(160))
    price_cdf: Mapped[int] = mapped_column(Integer)
    seats: Mapped[int] = mapped_column(Integer)
    duration_days: Mapped[int] = mapped_column(Integer)
    grace_days: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    revision: Mapped[int] = mapped_column(Integer)
    updated_by: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

@dataclass(frozen=True)
class CampusOffer:
    code: str
    label: str
    price_cdf: int
    seats: int
    duration_days: int
    grace_days: int
    active: bool
    revision: int

    def __post_init__(self):
        if (not self.code or len(self.code) > 64 or not all(c.isascii() and (c.isalnum() or c in '-_') for c in self.code)
            or not self.label.strip() or len(self.label) > 160 or self.price_cdf < 0
            or not 1 <= self.seats <= 100000 or not 1 <= self.duration_days <= 3660
            or not 0 <= self.grace_days <= 90 or self.revision < 1):
            raise ValueError('invalid_campus_offer')

class CampusOfferService:
    def __init__(self, sessions, governance, now):
        self.sessions = sessions
        self.governance = governance
        self.now = now

    def _require(self, actor_id):
        self.governance.require(actor_id, 'platform.roles.manage')

    def list(self, *, actor_id):
        self._require(actor_id)
        with self.sessions() as s:
            return [self._map(x) for x in s.scalars(select(CampusOfferRow).order_by(CampusOfferRow.code)).all()]

    def put(self, *, actor_id, offer: CampusOffer, expected_revision: int):
        self._require(actor_id)
        if expected_revision < 0:
            raise ValueError('invalid_expected_revision')
        with self.sessions.begin() as s:
            row = s.scalar(select(CampusOfferRow).where(CampusOfferRow.code == offer.code).with_for_update())
            revision = row.revision if row else 0
            if revision != expected_revision:
                raise ValueError('campus_offer_revision_conflict')
            if offer.revision != revision + 1:
                raise ValueError('campus_offer_revision_conflict')
            if row is None:
                row = CampusOfferRow(code=offer.code)
                s.add(row)
            row.label = offer.label.strip()
            row.price_cdf = offer.price_cdf
            row.seats = offer.seats
            row.duration_days = offer.duration_days
            row.grace_days = offer.grace_days
            row.active = offer.active
            row.revision = offer.revision
            row.updated_by = actor_id
            row.updated_at = self.now()
        return offer

    @staticmethod
    def _map(row):
        return CampusOffer(row.code,row.label,row.price_cdf,row.seats,row.duration_days,row.grace_days,row.active,row.revision)
