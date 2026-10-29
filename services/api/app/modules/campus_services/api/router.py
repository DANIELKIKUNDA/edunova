"""Campus physical services API. Auth derives from bearer session; no user ID in input."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StrictInt
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext

router = APIRouter()

def call(fn):
    try:
        return fn()
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        status = 409 if any(term in message for term in ('conflict', 'exists', 'concurrent', 'unavailable', 'already_registered')) else 400
        raise HTTPException(status, message) from exc

def encode(obj):
    data = asdict(obj)
    for key, value in data.items():
        if isinstance(value, Enum):
            data[key] = value.value
        elif isinstance(value, datetime):
            data[key] = value.isoformat()
    return data

class ResourceInput(BaseModel):
    kind: str
    code: str
    name: str
    location: str = ''
    capacity: int = Field(default=1, ge=1, le=5000)

class BookingInput(BaseModel):
    resource_id: str
    purpose: str
    starts_at: datetime
    ends_at: datetime

class MaintenanceReportInput(BaseModel):
    resource_id: str
    description: str = Field(min_length=8, max_length=500)

class MaintenanceTransitionInput(BaseModel):
    expected_version: int = Field(ge=1)
    note: str = Field(default='', max_length=500)

class VersionInput(BaseModel):
    expected_version: int = Field(ge=1)

@router.get('/institutions/{institution_id}/alerts')
def personal_campus_alerts(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alerts.for_account(user.account_id, institution_id))


@router.get('/institutions/{institution_id}/resources')
def resources(institution_id: str, user: AuthContext = Depends(current_auth)):
    return [encode(item) for item in call(lambda: runtime.campus_services.list_resources(
        user.account_id, institution_id))]

@router.post('/institutions/{institution_id}/resources')
def resource_create(institution_id: str, data: ResourceInput,
                    user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.register_resource(
        user.account_id, institution_id, **data.model_dump())))

@router.post('/institutions/{institution_id}/resources/{resource_id}/deactivate')
def resource_deactivate(institution_id: str, resource_id: str, data: VersionInput,
                        user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.deactivate_resource(
        user.account_id, institution_id, resource_id, data.expected_version)))

@router.get('/institutions/{institution_id}/bookings')
def bookings(institution_id: str, resource_id: str | None = None,
             user: AuthContext = Depends(current_auth)):
    return [encode(item) for item in call(lambda: runtime.campus_services.list_bookings(
        user.account_id, institution_id, resource_id=resource_id))]

@router.post('/institutions/{institution_id}/bookings')
def booking_create(institution_id: str, data: BookingInput,
                   user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.book(
        user.account_id, institution_id, **data.model_dump())))

@router.post('/institutions/{institution_id}/bookings/{booking_id}/cancel')
def booking_cancel(institution_id: str, booking_id: str, data: VersionInput,
                   user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.cancel_booking(
        user.account_id, institution_id, booking_id, data.expected_version)))


class AcademicRoomAssignmentInput(BaseModel):
    calendar_event_id: str = Field(min_length=1, max_length=64)
    resource_id: str = Field(min_length=1, max_length=64)

class TeachingRoomInput(BaseModel):
    teaching_session_id: str = Field(min_length=1, max_length=64)
    resource_id: str = Field(min_length=1, max_length=64)

@router.get('/institutions/{institution_id}/academic-unassigned')
def academic_unassigned(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.unassigned_academic_sessions(
        user.account_id, institution_id))

@router.get('/institutions/{institution_id}/teaching-allocations')
def teaching_allocations(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.teaching_allocations(user.account_id, institution_id))

@router.post('/institutions/{institution_id}/teaching-allocations')
def teaching_allocation_add(institution_id: str, data: TeachingRoomInput,
                            user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.assign_teaching_room(
        user.account_id, institution_id, data.teaching_session_id, data.resource_id))

@router.post('/institutions/{institution_id}/teaching-allocations/{assignment_id}/release')
def teaching_allocation_release(institution_id: str, assignment_id: str, data: VersionInput,
                                user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.release_teaching_room(
        user.account_id, institution_id, assignment_id, data.expected_version))

@router.get('/institutions/{institution_id}/academic-allocations')
def academic_allocations(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.calendar_allocations(user.account_id, institution_id))

@router.post('/institutions/{institution_id}/academic-allocations')
def academic_allocation_add(institution_id: str, data: AcademicRoomAssignmentInput,
                            user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.assign_calendar_resource(
        user.account_id, institution_id, data.calendar_event_id, data.resource_id))

@router.post('/institutions/{institution_id}/academic-allocations/{allocation_id}/release')
def academic_allocation_release(institution_id: str, allocation_id: str, data: VersionInput,
                                user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_services.release_calendar_resource(
        user.account_id, institution_id, allocation_id, data.expected_version))

@router.get('/institutions/{institution_id}/maintenance')
def maintenance_list(institution_id: str, resource_id: str | None = None,
                     user: AuthContext = Depends(current_auth)):
    return [encode(ticket) for ticket in call(lambda: runtime.campus_services.maintenance_tickets(
        user.account_id, institution_id, resource_id))]

@router.post('/institutions/{institution_id}/maintenance')
def maintenance_report(institution_id: str, data: MaintenanceReportInput,
                       user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.report_maintenance(
        user.account_id, institution_id, data.resource_id, data.description)))

@router.post('/institutions/{institution_id}/maintenance/{ticket_id}/{action}')
def maintenance_transition(institution_id: str, ticket_id: str, action: str,
                           data: MaintenanceTransitionInput,
                           user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.campus_services.transition_maintenance(
        user.account_id, institution_id, ticket_id, data.expected_version,
        action, data.note)))


# University event attendance is attached to the existing academic calendar.
# Configure capacity only for kind=event; legacy events remain opt-out.
class EventCapacityInput(BaseModel):
    expected_version: StrictInt = Field(ge=1)
    capacity: StrictInt = Field(ge=0, le=5000)

@router.get('/institutions/{institution_id}/events')
def campus_events(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_events.list_events(user.account_id, institution_id))

@router.get('/institutions/{institution_id}/events/my-registrations')
def my_event_registrations(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_events.my_registrations(user.account_id, institution_id))

@router.put('/institutions/{institution_id}/events/{event_id}/capacity')
def event_capacity(institution_id: str, event_id: str, data: EventCapacityInput,
                   user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_events.configure(
        user.account_id, institution_id, event_id, data.expected_version, data.capacity))

@router.post('/institutions/{institution_id}/events/{event_id}/register')
def event_register(institution_id: str, event_id: str,
                   user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_events.register(user.account_id, institution_id, event_id))

@router.post('/institutions/{institution_id}/events/{event_id}/withdraw')
def event_withdraw(institution_id: str, event_id: str, data: VersionInput,
                   user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_events.cancel(
        user.account_id, institution_id, event_id, data.expected_version))


# Phase 16 Alumni: private applications, opt-in directory, audited staff approval.
class AlumniApplicationInput(BaseModel):
    display_name: str = Field(min_length=2, max_length=160)
    program_name: str = Field(min_length=2, max_length=160)
    graduation_year: StrictInt = Field(ge=1950, le=2100)
    headline: str = Field(default='', max_length=240)
    visible: bool = False
    expected_version: StrictInt = Field(default=0, ge=0)

class AlumniDecisionInput(BaseModel):
    expected_version: StrictInt = Field(ge=1)
    decision: str
    reference: str = Field(min_length=6, max_length=160)

class AlumniOpportunityInput(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10, max_length=2000)
    application_url: str = Field(default='', max_length=500)

@router.get('/alumni/my-institutions')
def my_verified_alumni_institutions(user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.my_institutions(user.account_id))

@router.get('/institutions/{institution_id}/alumni/me')
def alumni_me(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.my_profile(user.account_id, institution_id))

@router.put('/institutions/{institution_id}/alumni/me')
def alumni_apply(institution_id: str, data: AlumniApplicationInput,
                 user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.apply(user.account_id, institution_id, **data.model_dump()))

@router.get('/institutions/{institution_id}/alumni/directory')
def alumni_directory(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.directory(user.account_id, institution_id))

@router.get('/institutions/{institution_id}/alumni/pending')
def alumni_pending(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.pending(user.account_id, institution_id))

@router.post('/institutions/{institution_id}/alumni/{profile_id}/decide')
def alumni_decide(institution_id: str, profile_id: str, data: AlumniDecisionInput,
                  user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.decide(user.account_id, institution_id,
        profile_id, data.expected_version, data.decision, data.reference))

@router.get('/institutions/{institution_id}/alumni/opportunities')
def alumni_opportunities(institution_id: str, user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.opportunities(user.account_id, institution_id))

@router.post('/institutions/{institution_id}/alumni/opportunities')
def alumni_post_opportunity(institution_id: str, data: AlumniOpportunityInput,
                            user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.post_opportunity(user.account_id,
        institution_id, **data.model_dump()))

@router.post('/institutions/{institution_id}/alumni/opportunities/{opportunity_id}/withdraw')
def alumni_withdraw_opportunity(institution_id: str, opportunity_id: str, data: VersionInput,
                                user: AuthContext = Depends(current_auth)):
    return call(lambda: runtime.campus_alumni.withdraw_opportunity(user.account_id,
        institution_id, opportunity_id, data.expected_version))
