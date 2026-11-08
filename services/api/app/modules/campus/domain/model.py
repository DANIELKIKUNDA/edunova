from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

class InstitutionState(StrEnum): ACTIVE='active'; SUSPENDED='suspended'; ARCHIVED='archived'
class CampusRole(StrEnum): OWNER='owner'; RECTOR='rector'; ADMIN='admin'; ACADEMIC_ADMIN='academic_admin'; FACULTY_ADMIN='faculty_admin'; TEACHER='teacher'; STUDENT='student'; AUDITOR='auditor'
class MembershipState(StrEnum): INVITED='invited'; ACTIVE='active'; SUSPENDED='suspended'; REVOKED='revoked'
class UnitKind(StrEnum): CAMPUS='campus'; FACULTY='faculty'; DEPARTMENT='department'; PROGRAM='program'
class PeriodKind(StrEnum): ACADEMIC_YEAR='academic_year'; SEMESTER='semester'; TERM='term'

@dataclass(frozen=True,slots=True)
class Institution:
    id:str; slug:str; name:str; legal_name:str; country_code:str; city:str|None; logo_url:str|None; state:InstitutionState; row_version:int; created_by:str; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class AcademicUnit:
    id:str; institution_id:str; kind:UnitKind; name:str; code:str; parent_id:str|None; active:bool; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class AcademicPeriod:
    id:str; institution_id:str; kind:PeriodKind; name:str; starts_on:date; ends_on:date; parent_id:str|None; active:bool; row_version:int; created_at:datetime
@dataclass(frozen=True,slots=True)
class Membership:
    id:str; institution_id:str; account_id:str; role:CampusRole; state:MembershipState; unit_id:str|None; invited_by:str|None; joined_at:datetime|None; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class Cohort:
    id:str; institution_id:str; program_unit_id:str; academic_period_id:str; name:str; level:str; active:bool; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class Enrollment:
    id:str; institution_id:str; cohort_id:str; student_account_id:str; active:bool; created_at:datetime
