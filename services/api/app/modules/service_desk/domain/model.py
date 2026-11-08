from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class RequestKind(StrEnum): ATTESTATION='attestation'; TRANSCRIPT='transcript'; DIPLOMA='diploma'; CERTIFICATE='certificate'; DUPLICATE='duplicate'; ADMIN_CORRECTION='admin_correction'; APPEAL='appeal'; OTHER='other'
class RequestState(StrEnum): SUBMITTED='submitted'; IN_REVIEW='in_review'; ACTION_REQUIRED='action_required'; APPROVED='approved'; REJECTED='rejected'; FULFILLED='fulfilled'; CANCELLED='cancelled'
@dataclass(frozen=True)
class ServiceRequest:
 id:str; institution_id:str; student_id:str; requester_account_id:str; kind:RequestKind; subject:str; details:str; state:RequestState; assigned_to:str|None; decision_reason:str|None; output_document_ref:str|None; output_sha256:str|None; version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class RequestEvent:
 id:str; request_id:str; actor_id:str; event_type:str; note:str|None; created_at:datetime
