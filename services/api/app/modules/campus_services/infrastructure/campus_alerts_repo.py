"""Account-scoped evidence for Campus alerts (no cross-tenant aggregation).

Queries are deliberately scoped by *both* tenant and authenticated account,
including for university administrators. No notification delivery is attempted.
"""
from __future__ import annotations

from sqlalchemy import select
from app.modules.campus_services.infrastructure.physical_library_repo import PhysicalLoanRow
from app.modules.campus_services.infrastructure.sqlalchemy_repo import CampusBookingRow
from app.modules.campus_services.infrastructure.event_registration_repo import CampusEventRegistrationRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow


class SqlCampusAlertsRepository:
    def __init__(self, sf):
        self.sf = sf

    def evidence(self, institution: str, account: str):
        with self.sf() as s:
            loans = s.scalars(select(PhysicalLoanRow).where(
                PhysicalLoanRow.institution_id == institution,
                PhysicalLoanRow.borrower_account_id == account,
                PhysicalLoanRow.returned_at.is_(None))
                .order_by(PhysicalLoanRow.due_at, PhysicalLoanRow.id).limit(100)).all()
            bookings = s.scalars(select(CampusBookingRow).where(
                CampusBookingRow.institution_id == institution,
                CampusBookingRow.requested_by == account,
                CampusBookingRow.state == 'cancelled',
                CampusBookingRow.cancellation_reason == 'resource_maintenance')
                .order_by(CampusBookingRow.updated_at.desc()).limit(100)).all()
            events = s.execute(select(CampusEventRegistrationRow, CalendarEventRow).join(
                CalendarEventRow, CampusEventRegistrationRow.event_id == CalendarEventRow.id)
                .where(CampusEventRegistrationRow.institution_id == institution,
                       CalendarEventRow.institution_id == institution,
                       CampusEventRegistrationRow.account_id == account,
                       CampusEventRegistrationRow.state == 'registered',
                       CalendarEventRow.kind == 'event',
                       CalendarEventRow.state.in_(['scheduled', 'cancelled']))
                .order_by(CalendarEventRow.starts_at.desc()).limit(100)).all()
            # Plain internal tuples. The public response never exposes account IDs.
            return ([(x.id, x.due_at) for x in loans],
                    [(x.id, x.ends_at, x.updated_at) for x in bookings],
                    [(e.id, e.starts_at, e.ends_at, e.state) for _, e in events])
