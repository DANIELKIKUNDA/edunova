"""Opt-in university events, reusing the existing Campus Operations calendar.

No parallel calendar or autonomous invitation subsystem is introduced.
"""
from __future__ import annotations
import uuid
from app.modules.campus.domain.model import CampusRole
from app.modules.campus_services.application.service import CampusServicesService

class CampusEventRegistrationService:
    def __init__(self, repo, campus_services: CampusServicesService, calendar, now, audit=None):
        self.repo, self.services, self.calendar, self.now, self.audit = (
            repo, campus_services, calendar, now, audit)

    def _member(self, account, institution):
        return self.services._member(account, institution)

    def _visible(self, account, institution, event_id):
        # Use the existing cohort visibility semantics from Campus Operations.
        for event in self.calendar.calendar(account, institution):
            if event.id == event_id:
                return event
        raise ValueError('campus_event_not_found')

    def _audit(self, account, action, event_id):
        if self.audit:
            self.audit.write(actor_account_id=account, action=action,
                             target_type='campus_event', target_id=event_id, metadata={})

    def list_events(self, account, institution):
        self._member(account, institution)
        events = self.calendar.calendar(account, institution)
        summaries = self.repo.summaries(institution, [event.id for event in events],
                                        account, self.now())
        return [{
            'id': event.id, 'title': event.title, 'details': event.details,
            'kind': event.kind.value, 'state': event.state.value,
            'starts_at': event.starts_at.isoformat(), 'ends_at': event.ends_at.isoformat(),
            'location': event.location, 'row_version': event.row_version,
            'cohort_id': event.cohort_id,
            **summaries.get(event.id, {})
        } for event in events if event.kind.value == 'event']

    def configure(self, account, institution, event_id, expected_version, capacity):
        self.services._staff(account, institution)
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_event_version_invalid')
        if type(capacity) is not int or not 0 <= capacity <= 5000:
            raise ValueError('campus_event_capacity_invalid')
        self._visible(account, institution, event_id)
        result = self.repo.configure(institution, event_id, expected_version, capacity, self.now())
        self._audit(account, 'campus.event.capacity_updated', event_id)
        return result

    def register(self, account, institution, event_id):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_event_auditor_read_only')
        self._visible(account, institution, event_id)
        result = self.repo.join(institution, event_id, account, self.now(),
                                'evr_' + uuid.uuid4().hex)
        self._audit(account, 'campus.event.registered', event_id)
        return result

    def cancel(self, account, institution, event_id, expected_version):
        member = self._member(account, institution)
        if member.role == CampusRole.AUDITOR:
            raise PermissionError('campus_event_auditor_read_only')
        if type(expected_version) is not int or expected_version < 1:
            raise ValueError('campus_event_version_invalid')
        # Do not require calendar visibility: someone leaving a cohort must still
        # be able to cancel their own existing registration, never another's.
        result = self.repo.cancel(institution, event_id, account, expected_version, self.now())
        self._audit(account, 'campus.event.registration_cancelled', event_id)
        return result

    def my_registrations(self, account, institution):
        self._member(account, institution)
        return self.repo.list_for_account(institution, account)
