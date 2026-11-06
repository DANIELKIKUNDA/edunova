from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class CourseState(StrEnum): DRAFT='draft'; PUBLISHED='published'; ARCHIVED='archived'
class SessionState(StrEnum): PLANNED='planned'; COMPLETED='completed'; CANCELLED='cancelled'
class ResourceState(StrEnum): DRAFT='draft'; PUBLISHED='published'; RETIRED='retired'
class TeacherRole(StrEnum): LEAD='lead'; CO_TEACHER='co_teacher'; ASSISTANT='assistant'
class SyllabusState(StrEnum): DRAFT='draft'; APPROVED='approved'; SUPERSEDED='superseded'
class TopicState(StrEnum): PLANNED='planned'; IN_PROGRESS='in_progress'; TAUGHT='taught'; SKIPPED='skipped'

@dataclass(frozen=True,slots=True)
class Course:
 id:str; institution_id:str; code:str; title:str; description:str; credits:int|None; state:CourseState; row_version:int; created_by:str; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class CourseOffering:
 id:str; institution_id:str; course_id:str; cohort_id:str; academic_period_id:str; label:str; state:CourseState; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class TeacherAssignment:
 id:str; institution_id:str; offering_id:str; teacher_account_id:str; role:TeacherRole; active:bool; created_at:datetime
@dataclass(frozen=True,slots=True)
class TeachingSession:
 id:str; institution_id:str; offering_id:str; title:str; starts_at:datetime; ends_at:datetime; state:SessionState; summary:str; next_topic:str; row_version:int; created_by:str; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class CourseResource:
 id:str; institution_id:str; offering_id:str; title:str; resource_type:str; uri:str; source_revision:str|None; state:ResourceState; row_version:int; created_by:str; created_at:datetime; updated_at:datetime

@dataclass(frozen=True,slots=True)
class Syllabus:
 id:str; institution_id:str; offering_id:str; version:int; title:str; overview:str; learning_outcomes:tuple[str,...]; state:SyllabusState; row_version:int; created_by:str; approved_by:str|None; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class SyllabusTopic:
 id:str; institution_id:str; syllabus_id:str; position:int; title:str; description:str; learning_objectives:tuple[str,...]; concept_refs:tuple[str,...]; planned_minutes:int; state:TopicState; row_version:int; updated_at:datetime
@dataclass(frozen=True,slots=True)
class ResourceRevision:
 id:str; institution_id:str; resource_id:str; revision_no:int; title:str; uri:str; source_revision:str|None; change_note:str; created_by:str; created_at:datetime
