from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class ApplicationState(StrEnum):
    DRAFT='draft'; READY='ready'; SUBMITTED='submitted'; WITHDRAWN='withdrawn'
class DocumentState(StrEnum):
    PENDING='pending'; UPLOADED='uploaded'; REPLACED='replaced'; DELETED='deleted'
class ConsentKind(StrEnum):
    PRIVACY='privacy'; APPLICATION_DECLARATION='application_declaration'

@dataclass(frozen=True)
class ApplicationConsent:
    id:str; application_id:str; kind:ConsentKind; policy_version:str; accepted_at:datetime; evidence_hash:str

@dataclass(frozen=True)
class SubmissionSnapshot:
    id:str; application_id:str; row_version:int; payload_sha256:str; document_manifest_sha256:str; created_at:datetime

@dataclass(frozen=True)
class CandidateApplication:
    id:str; account_id:str; institution_id:str; campaign_id:str; state:ApplicationState
    given_names:str; family_name:str; birth_date:str|None; nationality_code:str|None; gender:str|None
    address:str|None; city:str|None; country_code:str|None; phone_number:str|None; email:str|None
    row_version:int; created_at:datetime; updated_at:datetime; submitted_at:datetime|None=None; withdrawn_at:datetime|None=None

@dataclass(frozen=True)
class ApplicationDocument:
    id:str; application_id:str; requirement_code:str; original_name:str; content_type:str; size_bytes:int
    sha256:str; storage_key:str; state:DocumentState; created_at:datetime; replaced_by:str|None=None
@dataclass(frozen=True)
class UploadSession:
    id:str; application_id:str; requirement_code:str; original_name:str; content_type:str; total_bytes:int; total_chunks:int; expected_sha256:str|None; created_at:datetime; expires_at:datetime; completed_at:datetime|None=None
