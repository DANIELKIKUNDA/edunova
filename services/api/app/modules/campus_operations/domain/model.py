from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class AttendanceSessionState(StrEnum): DRAFT='draft'; OPEN='open'; CLOSED='closed'; CANCELLED='cancelled'
class AttendanceStatus(StrEnum): PRESENT='present'; LATE='late'; ABSENT='absent'; JUSTIFIED='justified'
class AttendanceReview(StrEnum): CLEAR='clear'; NEEDS_REVIEW='needs_review'; CONFIRMED='confirmed'; REJECTED='rejected'
class ProximityMode(StrEnum): NONE='none'; SIGNED_BEACON='signed_beacon'
class AnnouncementState(StrEnum): DRAFT='draft'; SCHEDULED='scheduled'; PUBLISHED='published'; RETRACTED='retracted'
class AbsenceRequestState(StrEnum): PENDING='pending'; APPROVED='approved'; REJECTED='rejected'; WITHDRAWN='withdrawn'
class CalendarEventKind(StrEnum): SESSION='session'; EXAM='exam'; DEADLINE='deadline'; EVENT='event'; CHANGE='change'
class CalendarEventState(StrEnum): SCHEDULED='scheduled'; CANCELLED='cancelled'; COMPLETED='completed'
@dataclass(frozen=True,slots=True)
class AttendancePolicy:
 id:str; institution_id:str; qr_ttl_seconds:int; require_device_binding:bool; require_location:bool; location_latitude:float|None; location_longitude:float|None; radius_meters:int; max_accuracy_meters:int; require_network_proof:bool; proximity_mode:ProximityMode; proximity_ttl_seconds:int; row_version:int; updated_at:datetime
@dataclass(frozen=True,slots=True)
class AttendanceSession:
 id:str; institution_id:str; teaching_session_id:str; offering_id:str; state:AttendanceSessionState; opens_at:datetime; closes_at:datetime; qr_epoch:int; row_version:int; created_by:str; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class AttendanceRecord:
 id:str; institution_id:str; attendance_session_id:str; student_account_id:str; status:AttendanceStatus; recorded_at:datetime; method:str; device_id:str|None; risk_score:int; review:AttendanceReview; evidence:str; row_version:int; updated_at:datetime
@dataclass(frozen=True,slots=True)
class Announcement:
 id:str; institution_id:str; offering_id:str|None; title:str; body:str; audience:str; state:AnnouncementState; publish_at:datetime; published_at:datetime|None; created_by:str; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class AbsenceRequest:
 id:str; institution_id:str; attendance_session_id:str; student_account_id:str; reason:str; evidence_uri:str|None; state:AbsenceRequestState; decision_reason:str|None; decided_by:str|None; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class CalendarEvent:
 id:str; institution_id:str; offering_id:str|None; cohort_id:str|None; kind:CalendarEventKind; title:str; details:str; starts_at:datetime; ends_at:datetime; location:str|None; state:CalendarEventState; source_ref:str|None; row_version:int; created_by:str; created_at:datetime; updated_at:datetime
