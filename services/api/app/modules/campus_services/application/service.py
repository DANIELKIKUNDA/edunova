"""Business rules for university physical-resource reservations.

Physical rooms and lab/equipment reservations complement existing campus
calendar and teaching timetable; they do not replace those modules.
"""
from __future__ import annotations
import uuid
from datetime import timedelta, timezone
from app.modules.campus.domain.model import CampusRole, MembershipState, InstitutionState
from app.modules.campus_services.domain.model import CampusResource, CampusBooking, ResourceKind, BookingState, MaintenanceTicket, MaintenanceState

_STAFF = frozenset({CampusRole.OWNER, CampusRole.RECTOR, CampusRole.ADMIN, CampusRole.ACADEMIC_ADMIN})
_VIEW_STAFF = _STAFF | {CampusRole.FACULTY_ADMIN, CampusRole.AUDITOR}

class CampusServicesService:
    def __init__(self, repo, campus, now, audit=None):
        self.repo, self.campus, self.now, self.audit = repo, campus, now, audit

    def _member(self, account: str, institution: str):
        membership = self.campus.membership(institution, account)
        if not membership or membership.state != MembershipState.ACTIVE:
            raise PermissionError('campus_active_membership_required')
        institution_row = self.campus.institution(institution)
        if institution_row is None or institution_row.state != InstitutionState.ACTIVE:
            raise PermissionError('campus_institution_not_active')
        # Only the current tenant's active member AND active institution grant visibility.
        return membership

    def _staff(self, account: str, institution: str):
        member = self._member(account, institution)
        if member.role not in _STAFF:
            raise PermissionError('campus_services_administrator_required')
        return member

    def _audit(self, account, action, target, id):
        if self.audit:
            self.audit.write(actor_account_id=account, action=action,
                             target_type=target, target_id=id, metadata={})

    def register_resource(self, account, institution, *, kind, code, name, location='', capacity=1):
        self._staff(account, institution)
        try:
            resource_kind = ResourceKind(kind)
        except ValueError:
            raise ValueError('campus_resource_kind_invalid') from None
        code, name, location = code.strip().upper(), name.strip(), location.strip()
        if not 1 <= len(code) <= 40 or not 1 <= len(name) <= 180 or len(location) > 240:
            raise ValueError('campus_resource_fields_invalid')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or not 1 <= capacity <= 5000:
            raise ValueError('campus_resource_capacity_invalid')
        now = self.now()
        resource = CampusResource('res_' + uuid.uuid4().hex, institution, resource_kind,
                                  code, name, location, capacity, True, 1, now, now)
        self.repo.add_resource(resource)
        self._audit(account, 'campus.resource.created', 'campus_resource', resource.id)
        return resource

    def list_resources(self, account, institution):
        self._member(account, institution)
        return tuple(r for r in self.repo.resources(institution) if r.active)

    def maintenance_tickets(self, account, institution, resource_id=None):
        member = self._member(account, institution)
        if resource_id and not any(r.id == resource_id for r in self.repo.resources(institution)):
            raise ValueError('campus_resource_not_found')
        owner = None if member.role in (_VIEW_STAFF - {CampusRole.FACULTY_ADMIN}) else account
        return self.repo.maintenance_tickets(institution, resource_id, reported_by=owner)

    def report_maintenance(self, account, institution, resource_id, description):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_services_auditor_read_only')
        if not isinstance(description, str) or not 8 <= len(description.strip()) <= 500:
            raise ValueError('campus_maintenance_description_invalid')
        now = self.now()
        ticket = MaintenanceTicket('mnt_' + uuid.uuid4().hex, institution, resource_id,
                                   account, description.strip(), MaintenanceState.REPORTED,
                                   '', 1, now, now)
        result = self.repo.report_maintenance(ticket)
        self._audit(account, 'campus.maintenance.reported', 'campus_maintenance', result.id)
        return result

    def transition_maintenance(self, account, institution, ticket_id, expected_version, action, note=''):
        self._staff(account, institution)
        if not isinstance(expected_version, int) or isinstance(expected_version, bool) or expected_version < 1:
            raise ValueError('campus_maintenance_version_invalid')
        if action not in {'start', 'resolve', 'dismiss'}:
            raise ValueError('campus_maintenance_action_invalid')
        if not isinstance(note, str) or len(note.strip()) > 500 or (
            action in {'resolve', 'dismiss'} and len(note.strip()) < 8):
            raise ValueError('campus_maintenance_resolution_invalid')
        result = self.repo.transition_maintenance(
            institution, ticket_id, expected_version, action, note.strip(), self.now())
        self._audit(account, 'campus.maintenance.' + action, 'campus_maintenance', result.id)
        return result

    def deactivate_resource(self, account, institution, resource_id, expected_version):
        self._staff(account, institution)
        if not isinstance(expected_version, int) or expected_version < 1:
            raise ValueError('campus_resource_version_invalid')
        resource = self.repo.deactivate_resource(institution, resource_id, expected_version, self.now())
        self._audit(account, 'campus.resource.deactivated', 'campus_resource', resource.id)
        return resource

    def book(self, account, institution, *, resource_id, purpose, starts_at, ends_at):
        member = self._member(account, institution)
        # Auditors are strictly read-only. Other active campus members can request a resource.
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_services_auditor_read_only')
        purpose = purpose.strip()
        if not 1 <= len(purpose) <= 240:
            raise ValueError('campus_booking_purpose_invalid')
        if (starts_at.tzinfo is None or ends_at.tzinfo is None or
            starts_at.utcoffset() is None or ends_at.utcoffset() is None):
            raise ValueError('campus_booking_timezone_required')
        now = self.now()
        if (starts_at < now or starts_at > now + timedelta(days=90) or
            ends_at <= starts_at or ends_at - starts_at > timedelta(hours=8)):
            raise ValueError('campus_booking_window_invalid')
        booking = CampusBooking('bkg_' + uuid.uuid4().hex, institution, resource_id, account,
                                purpose, starts_at.astimezone(timezone.utc),
                                ends_at.astimezone(timezone.utc), BookingState.CONFIRMED, 1,
                                now, now)
        # Repository locks parent resource and checks overlap inside ONE transaction.
        self.repo.add_booking(booking)
        self._audit(account, 'campus.booking.created', 'campus_booking', booking.id)
        return booking

    def unassigned_academic_sessions(self, account, institution):
        self._staff(account, institution)
        return self.repo.unassigned_academic_sessions(institution, self.now())

    def teaching_allocations(self, account, institution):
        self._staff(account, institution)
        return self.repo.teaching_allocations(institution)

    def assign_teaching_room(self, account, institution, teaching_session_id, resource_id):
        self._staff(account, institution)
        result = self.repo.assign_teaching_room(institution, teaching_session_id,
                                                 resource_id, account, self.now())
        self._audit(account, 'campus.teaching_room.assigned', 'campus_teaching_room', result['id'])
        return result

    def release_teaching_room(self, account, institution, assignment_id, expected_version):
        self._staff(account, institution)
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_teaching_version_invalid')
        result = self.repo.release_teaching_room(institution, assignment_id, expected_version)
        self._audit(account, 'campus.teaching_room.released', 'campus_teaching_room', assignment_id)
        return result

    def calendar_allocations(self, account, institution):
        self._staff(account, institution)
        return self.repo.academic_allocations(institution)

    def assign_calendar_resource(self, account, institution, event_id, resource_id):
        self._staff(account, institution)
        result = self.repo.assign_calendar_resource(institution, event_id, resource_id,
                                                   account, self.now())
        self._audit(account, 'campus.academic_resource.assigned', 'campus_academic_allocation', result['id'])
        return result

    def release_calendar_resource(self, account, institution, allocation_id, expected_version):
        self._staff(account, institution)
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_academic_version_invalid')
        result = self.repo.release_calendar_resource(institution, allocation_id, expected_version)
        self._audit(account, 'campus.academic_resource.released', 'campus_academic_allocation', allocation_id)
        return result

    def list_bookings(self, account, institution, *, resource_id=None):
        member = self._member(account, institution)
        # Apply row-level visibility in SQL BEFORE pagination. A student must
        # never lose their own bookings because other users filled the first page.
        owner = None if member.role in (_VIEW_STAFF - {CampusRole.FACULTY_ADMIN}) else account
        return self.repo.bookings(institution, resource_id=resource_id, requested_by=owner)

    def cancel_booking(self, account, institution, booking_id, expected_version):
        member = self._member(account, institution)
        current = self.repo.booking(institution, booking_id)
        if current is None:
            raise ValueError('campus_booking_not_found')
        if current.requested_by != account and member.role not in _STAFF:
            raise PermissionError('campus_booking_owner_required')
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_services_auditor_read_only')
        booking = self.repo.cancel_booking(institution, booking_id, expected_version, self.now())
        self._audit(account, 'campus.booking.cancelled', 'campus_booking', booking.id)
        return booking
