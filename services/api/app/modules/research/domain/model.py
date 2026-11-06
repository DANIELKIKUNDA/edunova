from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class ResearchKind(StrEnum): TFC='tfc'; MEMOIRE='memoire'; THESE='these'
class ResearchState(StrEnum): PROPOSED='proposed'; APPROVED='approved'; IN_PROGRESS='in_progress'; READY_FOR_DEFENSE='ready_for_defense'; DEFENDED='defended'; CANCELLED='cancelled'
class RevisionState(StrEnum): SUBMITTED='submitted'; CHANGES_REQUESTED='changes_requested'; APPROVED='approved'
@dataclass(frozen=True)
class ResearchProject:
    id:str; institution_id:str; student_id:str; academic_registration_id:str; kind:ResearchKind; title:str; supervisor_account_id:str; state:ResearchState; version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class ResearchRevision:
    id:str; project_id:str; number:int; document_ref:str; sha256:str; state:RevisionState; student_note:str; reviewer_note:str|None; created_at:datetime; reviewed_at:datetime|None
@dataclass(frozen=True)
class Defense:
    id:str; project_id:str; scheduled_at:datetime; room:str; chair_account_id:str; secretary_account_id:str; status:str; decision:str|None; score:float|None; minutes_sha256:str|None; created_at:datetime
