"""Atomic resource booking repository.

PostgreSQL: SERIALIZE booking mutations by locking the resource parent row.
SQLite: sequential test adapter (SQLite ignores FOR UPDATE); PostgreSQL live
concurrency still requires Phase 23 machine certification.
"""
from datetime import UTC
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index, and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import CalendarEventRow
from app.modules.teaching.infrastructure.sqlalchemy_repo import SessionRow as TeachingSessionRow
from app.shared.infrastructure.database import Base
from app.modules.campus_services.domain.model import CampusResource, CampusBooking, ResourceKind, BookingState, MaintenanceTicket, MaintenanceState

def aware(t):
    return t if t.tzinfo is not None else t.replace(tzinfo=UTC)

class CampusResourceRow(Base):
    __tablename__ = 'campus_physical_resources'
    __table_args__ = (
        UniqueConstraint('institution_id', 'code', name='uq_physical_resource_institution_code'),
        CheckConstraint('capacity BETWEEN 1 AND 5000', name='ck_physical_resource_capacity'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180))
    location: Mapped[str] = mapped_column(String(240))
    capacity: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean)
    service_state: Mapped[str] = mapped_column(String(24), nullable=False, default='available')
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))

class CampusBookingRow(Base):
    __tablename__ = 'campus_resource_bookings'
    __table_args__ = (
        CheckConstraint('ends_at > starts_at', name='ck_campus_booking_time'),
        CheckConstraint("state IN ('confirmed','cancelled')", name='ck_campus_booking_state'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_physical_resources.id'), index=True)
    requested_by: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(240))
    starts_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(24))
    cancellation_reason: Mapped[str] = mapped_column(String(32), nullable=False, default='')
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))

class CampusMaintenanceRow(Base):
    __tablename__ = 'campus_resource_maintenance'
    __table_args__ = (
        CheckConstraint("status IN ('reported','in_progress','resolved','dismissed')", name='ck_campus_maintenance_status'),
        CheckConstraint('row_version >= 1', name='ck_campus_maintenance_version'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_physical_resources.id'), index=True)
    reported_by: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(24))
    resolution: Mapped[str] = mapped_column(String(500), default='')
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))

Index('uq_campus_maintenance_open_resource', CampusMaintenanceRow.resource_id, unique=True,
      postgresql_where=CampusMaintenanceRow.status.in_(['reported', 'in_progress']),
      sqlite_where=CampusMaintenanceRow.status.in_(['reported', 'in_progress']))

class AcademicResourceAllocationRow(Base):
    __tablename__ = 'campus_academic_resource_allocations'
    __table_args__ = (UniqueConstraint('calendar_event_id', name='uq_academic_resource_calendar_event'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    calendar_event_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_calendar_events.id'))
    resource_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_physical_resources.id'), index=True)
    assigned_by: Mapped[str] = mapped_column(String(64))
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))

class TeachingRoomAllocationRow(Base):
    __tablename__ = 'campus_teaching_room_allocations'
    __table_args__ = (UniqueConstraint('teaching_session_id', name='uq_campus_room_teaching_session'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    teaching_session_id: Mapped[str] = mapped_column(String(64), ForeignKey('teaching_sessions.id'))
    resource_id: Mapped[str] = mapped_column(String(64), ForeignKey('campus_physical_resources.id'), index=True)
    assigned_by: Mapped[str] = mapped_column(String(64))
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))

class SqlCampusServicesRepository:
    def __init__(self, session_factory):
        self.sf = session_factory

    @staticmethod
    def _r(row):
        return CampusResource(row.id, row.institution_id, ResourceKind(row.kind), row.code,
                              row.name, row.location, row.capacity, row.active,
                              row.row_version, aware(row.created_at), aware(row.updated_at), row.service_state)

    @staticmethod
    def _b(row):
        return CampusBooking(row.id, row.institution_id, row.resource_id, row.requested_by,
                             row.purpose, aware(row.starts_at), aware(row.ends_at),
                             BookingState(row.state), row.row_version,
                             aware(row.created_at), aware(row.updated_at), row.cancellation_reason)

    @staticmethod
    def _t(row):
        return MaintenanceTicket(row.id, row.institution_id, row.resource_id,
                                 row.reported_by, row.description, MaintenanceState(row.status),
                                 row.resolution, row.row_version,
                                 aware(row.created_at), aware(row.updated_at))

    def maintenance_tickets(self, institution, resource_id=None, reported_by=None):
        with self.sf() as session:
            query = select(CampusMaintenanceRow).where(CampusMaintenanceRow.institution_id == institution)
            if resource_id:
                query = query.where(CampusMaintenanceRow.resource_id == resource_id)
            if reported_by is not None:
                query = query.where(CampusMaintenanceRow.reported_by == reported_by)
            return tuple(self._t(row) for row in session.scalars(
                query.order_by(CampusMaintenanceRow.created_at.desc()).limit(250)).all())

    def report_maintenance(self, ticket):
        with self.sf.begin() as session:
            resource = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == ticket.resource_id,
                CampusResourceRow.institution_id == ticket.institution_id).with_for_update())
            if resource is None or not resource.active or resource.service_state != 'available':
                raise ValueError('campus_resource_unavailable')
            if session.scalar(select(CampusMaintenanceRow.id).where(
                CampusMaintenanceRow.resource_id == ticket.resource_id,
                CampusMaintenanceRow.status.in_(['reported','in_progress'])).limit(1)):
                raise ValueError('campus_maintenance_open_conflict')
            session.add(CampusMaintenanceRow(**{**{
                key: getattr(ticket, key) for key in ticket.__dataclass_fields__},
                'status': ticket.status.value}))
            try:
                session.flush()
            except IntegrityError:
                raise ValueError('campus_maintenance_open_conflict') from None
            return ticket

    def transition_maintenance(self, institution, ticket_id, expected_version, action, note, now):
        transitions = {
            'start': ('reported', 'in_progress'),
            'resolve': ('in_progress', 'resolved'),
            'dismiss': ('reported', 'dismissed'),
        }
        source, destination = transitions[action]
        with self.sf.begin() as session:
            ticket = session.scalar(select(CampusMaintenanceRow).where(
                CampusMaintenanceRow.id == ticket_id,
                CampusMaintenanceRow.institution_id == institution))
            if ticket is None:
                raise ValueError('campus_maintenance_not_found')
            # Always acquire the resource lock first, consistent with add_booking().
            resource = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == ticket.resource_id,
                CampusResourceRow.institution_id == institution).with_for_update())
            session.refresh(ticket)
            if ticket.row_version != expected_version or ticket.status != source:
                raise ValueError('campus_maintenance_concurrent_conflict')
            if resource is None or not resource.active:
                raise ValueError('campus_resource_unavailable')
            if action == 'start':
                if session.scalar(select(AcademicResourceAllocationRow.id).join(
                    CalendarEventRow, CalendarEventRow.id == AcademicResourceAllocationRow.calendar_event_id).where(
                    AcademicResourceAllocationRow.institution_id == institution,
                    AcademicResourceAllocationRow.resource_id == resource.id,
                    CalendarEventRow.institution_id == institution,
                    CalendarEventRow.state == 'scheduled', CalendarEventRow.ends_at > now).limit(1)):
                    raise ValueError('campus_maintenance_academic_conflict')
                if session.scalar(select(TeachingRoomAllocationRow.id).join(
                    TeachingSessionRow, TeachingSessionRow.id == TeachingRoomAllocationRow.teaching_session_id).where(
                    TeachingRoomAllocationRow.institution_id == institution,
                    TeachingRoomAllocationRow.resource_id == resource.id,
                    TeachingSessionRow.institution_id == institution,
                    TeachingSessionRow.state == 'planned', TeachingSessionRow.ends_at > now).limit(1)):
                    raise ValueError('campus_maintenance_teaching_conflict')
                if resource.service_state != 'available':
                    raise ValueError('campus_resource_unavailable')
                resource.service_state = 'maintenance'
                # Existing future reservations become visible as cancelled with a reason;
                # preserve historical past bookings, no silent deletion.
                session.execute(update(CampusBookingRow).where(
                    CampusBookingRow.institution_id == institution,
                    CampusBookingRow.resource_id == resource.id,
                    CampusBookingRow.state == 'confirmed',
                    CampusBookingRow.ends_at > now).values(
                    state='cancelled', cancellation_reason='resource_maintenance',
                    row_version=CampusBookingRow.row_version + 1, updated_at=now))
            elif action == 'resolve':
                if resource.service_state != 'maintenance':
                    raise ValueError('campus_maintenance_concurrent_conflict')
                resource.service_state = 'available'
            elif resource.service_state != 'available':
                raise ValueError('campus_maintenance_concurrent_conflict')
            resource.row_version += 1
            resource.updated_at = now
            ticket.status = destination
            ticket.resolution = note
            ticket.row_version += 1
            ticket.updated_at = now
            session.flush()
            return self._t(ticket)

    def resources(self, institution):
        with self.sf() as session:
            rows = session.scalars(select(CampusResourceRow).where(
                CampusResourceRow.institution_id == institution).order_by(CampusResourceRow.code)).all()
            return tuple(self._r(row) for row in rows)

    def add_resource(self, resource):
        values = {field: getattr(resource, field) for field in resource.__dataclass_fields__}
        values['kind'] = resource.kind.value
        try:
            with self.sf.begin() as session:
                session.add(CampusResourceRow(**values))
        except IntegrityError:
            raise ValueError('campus_resource_code_already_exists') from None

    def deactivate_resource(self, institution, resource_id, expected_version, now):
        with self.sf.begin() as session:
            row = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.institution_id == institution,
                CampusResourceRow.id == resource_id).with_for_update())
            if (row is None or not row.active or row.row_version != expected_version):
                raise ValueError('campus_resource_not_found_or_concurrent_modification')
            if row.service_state != 'available' or session.scalar(select(CampusMaintenanceRow.id).where(
                    CampusMaintenanceRow.resource_id == row.id,
                    CampusMaintenanceRow.status.in_(['reported','in_progress'])).limit(1)):
                raise ValueError('campus_maintenance_open_conflict')
            row.active = False
            row.row_version += 1
            row.updated_at = now
            session.flush()
            return self._r(row)

    def add_booking(self, booking):
        # Lock is acquired BEFORE checking overlapping bookings, preventing two
        # competing transactions from both observing an empty calendar in PG.
        with self.sf.begin() as session:
            resource = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == booking.resource_id,
                CampusResourceRow.institution_id == booking.institution_id).with_for_update())
            if resource is None or not resource.active or resource.service_state != 'available':
                raise ValueError('campus_resource_unavailable')
            collision = session.scalar(select(CampusBookingRow.id).where(
                CampusBookingRow.institution_id == booking.institution_id,
                CampusBookingRow.resource_id == booking.resource_id,
                CampusBookingRow.state == 'confirmed',
                CampusBookingRow.starts_at < booking.ends_at,
                CampusBookingRow.ends_at > booking.starts_at).limit(1))
            if collision:
                raise ValueError('campus_resource_booking_conflict')
            academic_collision = session.scalar(select(AcademicResourceAllocationRow.id).join(
                CalendarEventRow, CalendarEventRow.id == AcademicResourceAllocationRow.calendar_event_id).where(
                AcademicResourceAllocationRow.institution_id == booking.institution_id,
                AcademicResourceAllocationRow.resource_id == booking.resource_id,
                CalendarEventRow.institution_id == booking.institution_id,
                CalendarEventRow.state == 'scheduled',
                CalendarEventRow.starts_at < booking.ends_at,
                CalendarEventRow.ends_at > booking.starts_at).limit(1))
            if academic_collision:
                raise ValueError('campus_resource_academic_conflict')
            teaching_collision = session.scalar(select(TeachingRoomAllocationRow.id).join(
                TeachingSessionRow, TeachingSessionRow.id == TeachingRoomAllocationRow.teaching_session_id).where(
                TeachingRoomAllocationRow.institution_id == booking.institution_id,
                TeachingRoomAllocationRow.resource_id == booking.resource_id,
                TeachingSessionRow.institution_id == booking.institution_id,
                TeachingSessionRow.state == 'planned',
                TeachingSessionRow.starts_at < booking.ends_at,
                TeachingSessionRow.ends_at > booking.starts_at).limit(1))
            if teaching_collision:
                raise ValueError('campus_resource_teaching_conflict')
            values = {field: getattr(booking, field) for field in booking.__dataclass_fields__}
            values['state'] = booking.state.value
            session.add(CampusBookingRow(**values))

    def unassigned_academic_sessions(self, institution, now, limit=100):
        """Staff-only reconciliation queue, not an inferred room assignment.

        Only canonical scheduled/planned future sessions are exposed. A missing
        link is explicitly reported rather than assuming the free-text location
        identifies a real room. Counts are complete; rows are page-capped.
        """
        calendar_link = select(AcademicResourceAllocationRow.id).where(
            AcademicResourceAllocationRow.calendar_event_id == CalendarEventRow.id).exists()
        teaching_link = select(TeachingRoomAllocationRow.id).where(
            TeachingRoomAllocationRow.teaching_session_id == TeachingSessionRow.id).exists()
        calendar_query = select(CalendarEventRow).where(
            CalendarEventRow.institution_id == institution,
            CalendarEventRow.state == 'scheduled',
            CalendarEventRow.kind.in_(('session', 'exam', 'event')),
            CalendarEventRow.ends_at > now, ~calendar_link)
        teaching_query = select(TeachingSessionRow).where(
            TeachingSessionRow.institution_id == institution,
            TeachingSessionRow.state == 'planned',
            TeachingSessionRow.ends_at > now, ~teaching_link)
        from sqlalchemy import func
        with self.sf() as session:
            calendar_count = session.scalar(select(func.count()).select_from(
                calendar_query.subquery())) or 0
            teaching_count = session.scalar(select(func.count()).select_from(
                teaching_query.subquery())) or 0
            calendar = session.scalars(calendar_query.order_by(
                CalendarEventRow.starts_at, CalendarEventRow.id).limit(limit)).all()
            teaching = session.scalars(teaching_query.order_by(
                TeachingSessionRow.starts_at, TeachingSessionRow.id).limit(limit)).all()
        return dict(calendar_count=calendar_count, teaching_count=teaching_count,
            truncated=calendar_count > limit or teaching_count > limit,
            calendar=[dict(id=row.id, title=row.title,
                location_hint=row.location, starts_at=aware(row.starts_at).isoformat(),
                ends_at=aware(row.ends_at).isoformat()) for row in calendar],
            teaching=[dict(id=row.id, title=row.title,
                starts_at=aware(row.starts_at).isoformat(),
                ends_at=aware(row.ends_at).isoformat()) for row in teaching])

    def academic_allocations(self, institution):
        # Do not expose academic identifiers outside authorized staff routes.
        with self.sf() as session:
            rows = session.execute(select(AcademicResourceAllocationRow, CalendarEventRow).join(
                CalendarEventRow, CalendarEventRow.id == AcademicResourceAllocationRow.calendar_event_id).where(
                AcademicResourceAllocationRow.institution_id == institution,
                CalendarEventRow.institution_id == institution).order_by(CalendarEventRow.starts_at)).all()
            return [dict(id=a.id, calendar_event_id=e.id, resource_id=a.resource_id,
                         title=e.title, starts_at=aware(e.starts_at).isoformat(),
                         ends_at=aware(e.ends_at).isoformat(), state=e.state,
                         row_version=a.row_version) for a, e in rows]

    def assign_calendar_resource(self, institution, event_id, resource_id, assigned_by, now):
        from uuid import uuid4
        with self.sf.begin() as session:
            resource = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == resource_id,
                CampusResourceRow.institution_id == institution).with_for_update())
            if resource is None or not resource.active or resource.service_state != 'available':
                raise ValueError('campus_resource_unavailable')
            if resource.kind not in {'room', 'laboratory', 'library_space'}:
                raise ValueError('campus_academic_resource_kind_invalid')
            event = session.scalar(select(CalendarEventRow).where(
                CalendarEventRow.id == event_id, CalendarEventRow.institution_id == institution))
            if event is None or event.state != 'scheduled' or event.kind not in ('session', 'exam', 'event'):
                raise ValueError('campus_academic_event_not_eligible')
            if event.kind in ('session', 'exam') and not event.offering_id:
                raise ValueError('campus_academic_offering_required')
            if session.scalar(select(AcademicResourceAllocationRow.id).where(
                AcademicResourceAllocationRow.calendar_event_id == event_id).limit(1)):
                raise ValueError('campus_academic_event_already_assigned')
            if session.scalar(select(CampusBookingRow.id).where(
                CampusBookingRow.institution_id == institution,
                CampusBookingRow.resource_id == resource_id, CampusBookingRow.state == 'confirmed',
                CampusBookingRow.starts_at < event.ends_at,
                CampusBookingRow.ends_at > event.starts_at).limit(1)):
                raise ValueError('campus_resource_booking_conflict')
            if session.scalar(select(AcademicResourceAllocationRow.id).join(
                CalendarEventRow, CalendarEventRow.id == AcademicResourceAllocationRow.calendar_event_id).where(
                AcademicResourceAllocationRow.institution_id == institution,
                AcademicResourceAllocationRow.resource_id == resource_id,
                CalendarEventRow.institution_id == institution,
                CalendarEventRow.state == 'scheduled',
                CalendarEventRow.starts_at < event.ends_at,
                CalendarEventRow.ends_at > event.starts_at).limit(1)):
                raise ValueError('campus_resource_academic_conflict')
            if session.scalar(select(TeachingRoomAllocationRow.id).join(
                TeachingSessionRow, TeachingSessionRow.id == TeachingRoomAllocationRow.teaching_session_id).where(
                TeachingRoomAllocationRow.institution_id == institution,
                TeachingRoomAllocationRow.resource_id == resource_id,
                TeachingSessionRow.institution_id == institution,
                TeachingSessionRow.state == 'planned',
                TeachingSessionRow.starts_at < event.ends_at,
                TeachingSessionRow.ends_at > event.starts_at).limit(1)):
                raise ValueError('campus_resource_teaching_conflict')
            row = AcademicResourceAllocationRow(id='ars_'+uuid4().hex,
                institution_id=institution, calendar_event_id=event_id,
                resource_id=resource_id, assigned_by=assigned_by, row_version=1,
                created_at=now, updated_at=now)
            session.add(row)
            try:
                session.flush()
            except IntegrityError:
                raise ValueError('campus_academic_event_already_assigned') from None
            return dict(id=row.id, calendar_event_id=event.id, resource_id=resource_id,
                        title=event.title, starts_at=aware(event.starts_at).isoformat(),
                        ends_at=aware(event.ends_at).isoformat(), state=event.state,
                        row_version=1)

    def release_calendar_resource(self, institution, allocation_id, expected_version):
        with self.sf.begin() as session:
            allocation = session.scalar(select(AcademicResourceAllocationRow).where(
                AcademicResourceAllocationRow.id == allocation_id,
                AcademicResourceAllocationRow.institution_id == institution))
            if allocation is None:
                raise ValueError('campus_academic_allocation_not_found')
            # Same parent-resource lock order as booking and assignment.
            session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == allocation.resource_id,
                CampusResourceRow.institution_id == institution).with_for_update())
            session.refresh(allocation)
            if allocation.row_version != expected_version:
                raise ValueError('campus_academic_concurrent_conflict')
            session.delete(allocation)
            return dict(id=allocation_id, released=True)

    def teaching_allocations(self, institution):
        with self.sf() as session:
            pairs = session.execute(select(TeachingRoomAllocationRow, TeachingSessionRow).join(
                TeachingSessionRow, TeachingSessionRow.id == TeachingRoomAllocationRow.teaching_session_id).where(
                TeachingRoomAllocationRow.institution_id == institution,
                TeachingSessionRow.institution_id == institution).order_by(TeachingSessionRow.starts_at)).all()
            return [dict(id=row.id, teaching_session_id=t.id, resource_id=row.resource_id,
                title=t.title, starts_at=aware(t.starts_at).isoformat(),
                ends_at=aware(t.ends_at).isoformat(), state=t.state,
                row_version=row.row_version) for row, t in pairs]

    def assign_teaching_room(self, institution, teaching_session_id, resource_id, assigned_by, now):
        from uuid import uuid4
        with self.sf.begin() as session:
            resource = session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.id == resource_id,
                CampusResourceRow.institution_id == institution).with_for_update())
            if resource is None or not resource.active or resource.service_state != 'available':
                raise ValueError('campus_resource_unavailable')
            if resource.kind not in {'room', 'laboratory', 'library_space'}:
                raise ValueError('campus_academic_resource_kind_invalid')
            item = session.scalar(select(TeachingSessionRow).where(
                TeachingSessionRow.id == teaching_session_id,
                TeachingSessionRow.institution_id == institution))
            if item is None or item.state != 'planned':
                raise ValueError('campus_teaching_session_not_eligible')
            if session.scalar(select(TeachingRoomAllocationRow.id).where(
                TeachingRoomAllocationRow.teaching_session_id == teaching_session_id).limit(1)):
                raise ValueError('campus_teaching_session_already_assigned')
            if session.scalar(select(CampusBookingRow.id).where(
                CampusBookingRow.institution_id == institution,
                CampusBookingRow.resource_id == resource_id, CampusBookingRow.state == 'confirmed',
                CampusBookingRow.starts_at < item.ends_at,
                CampusBookingRow.ends_at > item.starts_at).limit(1)):
                raise ValueError('campus_resource_booking_conflict')
            if session.scalar(select(AcademicResourceAllocationRow.id).join(
                CalendarEventRow, CalendarEventRow.id == AcademicResourceAllocationRow.calendar_event_id).where(
                AcademicResourceAllocationRow.institution_id == institution,
                AcademicResourceAllocationRow.resource_id == resource_id,
                CalendarEventRow.institution_id == institution,
                CalendarEventRow.state == 'scheduled',
                CalendarEventRow.starts_at < item.ends_at,
                CalendarEventRow.ends_at > item.starts_at).limit(1)):
                raise ValueError('campus_resource_academic_conflict')
            if session.scalar(select(TeachingRoomAllocationRow.id).join(
                TeachingSessionRow, TeachingSessionRow.id == TeachingRoomAllocationRow.teaching_session_id).where(
                TeachingRoomAllocationRow.institution_id == institution,
                TeachingRoomAllocationRow.resource_id == resource_id,
                TeachingSessionRow.institution_id == institution,
                TeachingSessionRow.state == 'planned',
                TeachingSessionRow.starts_at < item.ends_at,
                TeachingSessionRow.ends_at > item.starts_at).limit(1)):
                raise ValueError('campus_resource_teaching_conflict')
            row = TeachingRoomAllocationRow(id='tra_'+uuid4().hex,
                institution_id=institution, teaching_session_id=teaching_session_id,
                resource_id=resource_id, assigned_by=assigned_by, row_version=1,
                created_at=now, updated_at=now)
            session.add(row)
            try: session.flush()
            except IntegrityError: raise ValueError('campus_teaching_session_already_assigned') from None
            return dict(id=row.id, teaching_session_id=item.id, resource_id=resource_id,
                        title=item.title, starts_at=aware(item.starts_at).isoformat(),
                        ends_at=aware(item.ends_at).isoformat(), state=item.state, row_version=1)

    def release_teaching_room(self, institution, assignment_id, version):
        with self.sf.begin() as session:
            item = session.scalar(select(TeachingRoomAllocationRow).where(
                TeachingRoomAllocationRow.institution_id == institution,
                TeachingRoomAllocationRow.id == assignment_id))
            if item is None:
                raise ValueError('campus_teaching_allocation_not_found')
            session.scalar(select(CampusResourceRow).where(
                CampusResourceRow.institution_id == institution,
                CampusResourceRow.id == item.resource_id).with_for_update())
            session.refresh(item)
            if item.row_version != version:
                raise ValueError('campus_teaching_concurrent_conflict')
            session.delete(item)
            return dict(id=assignment_id, released=True)

    def booking(self, institution, booking_id):
        with self.sf() as session:
            row = session.scalar(select(CampusBookingRow).where(
                CampusBookingRow.institution_id == institution,
                CampusBookingRow.id == booking_id))
            return self._b(row) if row else None

    def bookings(self, institution, resource_id=None, requested_by=None):
        with self.sf() as session:
            query = select(CampusBookingRow).where(CampusBookingRow.institution_id == institution)
            if resource_id is not None:
                query = query.where(CampusBookingRow.resource_id == resource_id)
            if requested_by is not None:
                query = query.where(CampusBookingRow.requested_by == requested_by)
            return tuple(self._b(row) for row in session.scalars(
                query.order_by(CampusBookingRow.starts_at.desc()).limit(250)).all())

    def cancel_booking(self, institution, booking_id, expected_version, now):
        with self.sf.begin() as session:
            result = session.execute(update(CampusBookingRow).where(
                CampusBookingRow.institution_id == institution, CampusBookingRow.id == booking_id,
                CampusBookingRow.row_version == expected_version,
                CampusBookingRow.state == 'confirmed').values(
                    state='cancelled', cancellation_reason='user_cancelled', row_version=expected_version + 1, updated_at=now))
            if result.rowcount != 1:
                raise ValueError('campus_booking_not_found_or_concurrent_modification')
            return self._b(session.get(CampusBookingRow, booking_id))
