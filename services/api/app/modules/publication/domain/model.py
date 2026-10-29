from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class ReleaseState(StrEnum):
    DRAFT="draft"; SCHEDULED="scheduled"; PUBLISHED="published"; WITHDRAWN="withdrawn"
class RolloutMode(StrEnum):
    ALL="all"; PERCENTAGE="percentage"; AUDIENCE="audience"
@dataclass(frozen=True)
class AcademicPlacement:
    country:str|None; institution:str|None; faculty_domain:str; program:str; curriculum_version:str|None; level:str; semester:str|None; ue:str|None; ecue:str|None; subject:str|None
@dataclass(frozen=True)
class PublicationRelease:
    id:str; editorial_item_id:str; editorial_revision_id:str; state:ReleaseState; version_label:str; placement_json:str; audience_json:str; rollout_mode:RolloutMode; rollout_percentage:int; premium_required:bool; offline_allowed:bool; scheduled_at:datetime|None; published_at:datetime|None; withdrawn_at:datetime|None; created_by:str; created_at:datetime; row_version:int=1
@dataclass(frozen=True)
class CatalogSnapshot:
    id:str; release_id:str; manifest_sha256:str; manifest_json:str; created_at:datetime
