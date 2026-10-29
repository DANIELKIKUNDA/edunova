"""Phase 16: institutional physical resources, distinct from the digital library."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class ResourceKind(StrEnum):
    ROOM = 'room'
    LABORATORY = 'laboratory'
    EQUIPMENT = 'equipment'
    LIBRARY_SPACE = 'library_space'

class BookingState(StrEnum):
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

@dataclass(frozen=True, slots=True)
class CampusResource:
    id: str
    institution_id: str
    kind: ResourceKind
    code: str
    name: str
    location: str
    capacity: int
    active: bool
    row_version: int
    created_at: datetime
    updated_at: datetime
    service_state: str = 'available'

@dataclass(frozen=True, slots=True)
class CampusBooking:
    id: str
    institution_id: str
    resource_id: str
    requested_by: str
    purpose: str
    starts_at: datetime
    ends_at: datetime
    state: BookingState
    row_version: int
    created_at: datetime
    updated_at: datetime
    cancellation_reason: str = ''


class MaintenanceState(StrEnum):
    REPORTED = 'reported'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    DISMISSED = 'dismissed'

@dataclass(frozen=True, slots=True)
class MaintenanceTicket:
    id: str
    institution_id: str
    resource_id: str
    reported_by: str
    description: str
    status: MaintenanceState
    resolution: str
    row_version: int
    created_at: datetime
    updated_at: datetime
