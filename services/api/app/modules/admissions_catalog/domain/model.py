from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class CampaignState(StrEnum): DRAFT='draft'; PUBLISHED='published'; CLOSED='closed'; ARCHIVED='archived'
@dataclass(frozen=True,slots=True)
class AdmissionCampaign:
 id:str; institution_id:str; program_unit_id:str; academic_year_id:str; curriculum_id:str; slug:str; title:str; summary:str; state:CampaignState; opens_at:datetime; closes_at:datetime; capacity:int|None; application_fee_minor:int; currency:str; contact_email:str|None; row_version:int; created_by:str; created_at:datetime; published_at:datetime|None; instructions:str=''; study_mode:str='on_campus'; campus_label:str|None=None; intake_label:str|None=None; eligibility_summary:str|None=None; archived_at:datetime|None=None
@dataclass(frozen=True,slots=True)
class AdmissionRequirement:
 id:str; campaign_id:str; code:str; label:str; description:str|None; required:bool; document_required:bool; ordinal:int
