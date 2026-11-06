"""Campus event registration over the *existing* academic calendar.

The event parent row is locked before capacity / enrollment mutations in PG;
SQLite tests only validate sequential behavior, not PostgreSQL concurrency.
"""
from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class CampusEventRegistrationRow(Base):
    __tablename__ = 'campus_event_registrations'
    __table_args__ = (
        UniqueConstraint('event_id', 'account_id', name='uq_campus_event_account'),
        CheckConstraint("state IN ('registered','cancelled')", name='ck_campus_event_registration_state'),
        CheckConstraint('row_version >= 1', name='ck_campus_event_registration_version'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_calendar_events.id'), index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SqlCampusEventRegistrationRepository:
    def __init__(self, sf):
        self.sf = sf

    @staticmethod
    def _serialize(row):
        return {'id': row.id, 'institution_id': row.institution_id, 'event_id': row.event_id,
                'account_id': row.account_id, 'state': row.state,
                'row_version': row.row_version,
                'created_at': _utc(row.created_at).isoformat(),
                'updated_at': _utc(row.updated_at).isoformat()}

    def list_for_account(self, institution, account):
        with self.sf() as session:
            rows = session.scalars(select(CampusEventRegistrationRow).where(
                CampusEventRegistrationRow.institution_id == institution,
                CampusEventRegistrationRow.account_id == account)
                .order_by(CampusEventRegistrationRow.created_at.desc()).limit(250)).all()
            return [self._serialize(row) for row in rows]

    def summaries(self, institution, event_ids, account, now):
        if not event_ids:
            return {}
        with self.sf() as session:
            events = session.scalars(select(CalendarEventRow).where(
                CalendarEventRow.institution_id == institution,
                CalendarEventRow.id.in_(event_ids))).all()
            counts = dict(session.execute(select(
                CampusEventRegistrationRow.event_id, func.count(CampusEventRegistrationRow.id))
                .where(CampusEventRegistrationRow.institution_id == institution,
                       CampusEventRegistrationRow.event_id.in_(event_ids),
                       CampusEventRegistrationRow.state == 'registered')
                .group_by(CampusEventRegistrationRow.event_id)).all())
            mine = {row.event_id: self._serialize(row) for row in session.scalars(
                select(CampusEventRegistrationRow).where(
                    CampusEventRegistrationRow.institution_id == institution,
                    CampusEventRegistrationRow.event_id.in_(event_ids),
                    CampusEventRegistrationRow.account_id == account)).all()}
            return {event.id: {
                'registration_capacity': event.registration_capacity,
                'registrations_count': counts.get(event.id, 0),
                'registration_open': event.kind == 'event' and event.state == 'scheduled'
                   and _utc(event.starts_at) > now and event.registration_capacity > 0
                   and counts.get(event.id, 0) < event.registration_capacity,
                'my_registration': mine.get(event.id),
            } for event in events}

    def configure(self, institution, event_id, expected_version, capacity, now):
        with self.sf.begin() as session:
            row = session.scalar(select(CalendarEventRow).where(
                CalendarEventRow.id == event_id,
                CalendarEventRow.institution_id == institution).with_for_update())
            if row is None:
                raise ValueError('campus_event_not_found')
            if row.row_version != expected_version:
                raise ValueError('campus_event_concurrent_conflict')
            if row.kind != 'event' or row.state != 'scheduled' or _utc(row.starts_at) <= now:
                raise ValueError('campus_event_registration_unavailable')
            occupied = session.scalar(select(func.count(CampusEventRegistrationRow.id)).where(
                CampusEventRegistrationRow.event_id == row.id,
                CampusEventRegistrationRow.institution_id == institution,
                CampusEventRegistrationRow.state == 'registered')) or 0
            if capacity < occupied:
                raise ValueError('campus_event_capacity_conflict')
            row.registration_capacity = capacity
            row.row_version += 1
            row.updated_at = now
            session.flush()
            return {'event_id': row.id, 'registration_capacity': capacity,
                    'row_version': row.row_version, 'registrations_count': occupied}

    def join(self, institution, event_id, account, now, registration_id):
        with self.sf.begin() as session:
            event = session.scalar(select(CalendarEventRow).where(
                CalendarEventRow.id == event_id,
                CalendarEventRow.institution_id == institution).with_for_update())
            if (event is None or event.kind != 'event' or event.state != 'scheduled'
                    or _utc(event.starts_at) <= now or event.registration_capacity <= 0):
                raise ValueError('campus_event_registration_unavailable')
            prior = session.scalar(select(CampusEventRegistrationRow).where(
                CampusEventRegistrationRow.event_id == event_id,
                CampusEventRegistrationRow.account_id == account).with_for_update())
            if prior is not None and prior.state == 'registered':
                raise ValueError('campus_event_already_registered')
            occupied = session.scalar(select(func.count(CampusEventRegistrationRow.id)).where(
                CampusEventRegistrationRow.event_id == event_id,
                CampusEventRegistrationRow.institution_id == institution,
                CampusEventRegistrationRow.state == 'registered')) or 0
            if occupied >= event.registration_capacity:
                raise ValueError('campus_event_capacity_conflict')
            if prior is not None:
                prior.state = 'registered'
                prior.row_version += 1
                prior.updated_at = now
                row = prior
            else:
                row = CampusEventRegistrationRow(id=registration_id, institution_id=institution,
                    event_id=event_id, account_id=account, state='registered', row_version=1,
                    created_at=now, updated_at=now)
                session.add(row)
            session.flush()
            return self._serialize(row)

    def cancel(self, institution, event_id, account, expected_version, now):
        with self.sf.begin() as session:
            # Lock event before registration in the same order as join/configure.
            event = session.scalar(select(CalendarEventRow).where(
                CalendarEventRow.id == event_id,
                CalendarEventRow.institution_id == institution).with_for_update())
            if event is None:
                raise ValueError('campus_event_not_found')
            row = session.scalar(select(CampusEventRegistrationRow).where(
                CampusEventRegistrationRow.institution_id == institution,
                CampusEventRegistrationRow.event_id == event_id,
                CampusEventRegistrationRow.account_id == account).with_for_update())
            if row is None:
                raise ValueError('campus_event_registration_not_found')
            if row.state != 'registered' or row.row_version != expected_version:
                raise ValueError('campus_event_registration_concurrent_conflict')
            # Cancellation remains possible even after an event is cancelled.
            row.state = 'cancelled'
            row.row_version += 1
            row.updated_at = now
            session.flush()
            return self._serialize(row)
