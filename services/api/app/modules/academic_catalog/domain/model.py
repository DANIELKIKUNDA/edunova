from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class CurriculumState(StrEnum): DRAFT='draft'; PUBLISHED='published'; RETIRED='retired'
@dataclass(frozen=True,slots=True)
class CurriculumVersion:
 id:str; institution_id:str; program_unit_id:str; code:str; title:str; version:int; state:CurriculumState; effective_academic_year_id:str; source_catalog_id:str|None; row_version:int; created_by:str; created_at:datetime; published_at:datetime|None; retired_at:datetime|None=None
@dataclass(frozen=True,slots=True)
class CurriculumCourse:
 id:str; curriculum_id:str; semester:int; ue_code:str; code:str|None; title:str; credits:float|None; total_hours:int|None; ordinal:int; cycle:str|None=None; level:str|None=None; ue_declared_credits:float|None=None; cmi:int|None=None; tp_td:int|None=None; tpe:int|None=None; percent:float|None=None
@dataclass(frozen=True,slots=True)
class Prerequisite:
 id:str; curriculum_id:str; course_id:str; required_course_id:str; minimum_status:str
@dataclass(frozen=True,slots=True)
class CurriculumCohortBinding:
 id:str; curriculum_id:str; cohort_id:str; bound_by:str; bound_at:datetime
