from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class EditorialRole(StrEnum):
    OWNER='owner'; EDITOR='editor'; REVIEWER='reviewer'; PUBLISHER='publisher'
class EditorialState(StrEnum):
    INGESTED='ingested'; DRAFT='draft'; IN_REVIEW='in_review'; CHANGES_REQUESTED='changes_requested'; APPROVED='approved'; PUBLISHED='published'; ARCHIVED='archived'; REJECTED='rejected'
class ContentKind(StrEnum):
    COURSE='course'; ASSESSMENT='assessment'; QUESTION_SET='question_set'; SUMMARY='summary'; FLASHCARDS='flashcards'; SOLUTION='solution'; AUDIO_SCRIPT='audio_script'; OTHER='other'
class RightsStatus(StrEnum):
    UNKNOWN='unknown'; INTERNAL_ONLY='internal_only'; AUTHORIZED='authorized'; PUBLIC_DOMAIN='public_domain'; RESTRICTED='restricted'
class RiskLevel(StrEnum):
    STANDARD='standard'; MEDICAL='medical'; HIGH_STAKES='high_stakes'
class AssignmentStage(StrEnum):
    REVIEW='review'; PUBLICATION='publication'; EDITING='editing'

@dataclass(frozen=True)
class EditorialMember:
    account_id:str; role:EditorialRole; active:bool=True
@dataclass(frozen=True)
class EditorialItem:
    id:str; kind:ContentKind; title:str; faculty_domain:str; program:str; level:str; semester:str|None; state:EditorialState; risk:RiskLevel; rights_status:RightsStatus; rights_note:str; source_fingerprint:str; created_by:str; created_at:datetime; updated_at:datetime; current_revision_id:str|None=None; published_revision_id:str|None=None; row_version:int=1
@dataclass(frozen=True)
class EditorialRevision:
    id:str; item_id:str; revision_no:int; payload_json:str; source_fingerprint:str; ai_generated:bool; prompt_version:str|None; created_by:str; created_at:datetime; note:str=''
@dataclass(frozen=True)
class ReviewDecision:
    id:str; item_id:str; revision_id:str; reviewer_id:str; decision:str; comment:str; created_at:datetime; checklist_json:str='{}'; quality_score:int|None=None
@dataclass(frozen=True)
class PublicationRecord:
    id:str; item_id:str; revision_id:str; publisher_id:str; published_at:datetime; changelog:str
@dataclass(frozen=True)
class EditorialSource:
    id:str; item_id:str; filename:str; mime_type:str|None; checksum_sha256:str; size_bytes:int|None; storage_locator:str|None; ocr_confidence:float|None; human_verified:bool; imported_by:str; created_at:datetime
@dataclass(frozen=True)
class EditorialAssignment:
    id:str; item_id:str; stage:AssignmentStage; assignee_id:str; assigned_by:str; due_at:datetime|None; active:bool; created_at:datetime
@dataclass(frozen=True)
class QualityGateResult:
    code:str; passed:bool; label:str; detail:str=''
