from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class ReviewState(StrEnum): PENDING='pending'; IN_REVIEW='in_review'; CORRECTION_REQUIRED='correction_required'; COMPLETE='complete'; ELIGIBLE='eligible'; WAITLISTED='waitlisted'; ADMITTED='admitted'; REFUSED='refused'; WITHDRAWN='withdrawn'
class DocumentReviewState(StrEnum): PENDING='pending'; ACCEPTED='accepted'; REJECTED='rejected'; CORRECTION_REQUIRED='correction_required'
@dataclass(frozen=True)
class AdmissionReview:
 id:str; application_id:str; institution_id:str; state:ReviewState; assigned_to:str|None; decision_reason:str|None; row_version:int; created_at:datetime; updated_at:datetime; decided_at:datetime|None=None
@dataclass(frozen=True)
class DocumentReview:
 id:str; review_id:str; document_id:str; state:DocumentReviewState; note:str|None; reviewed_by:str; reviewed_at:datetime
@dataclass(frozen=True)
class AdmissionCommittee:
 id:str; institution_id:str; campaign_id:str; name:str; chair_account_id:str; quorum:int; active:bool; created_at:datetime
@dataclass(frozen=True)
class CommitteeMember:
 committee_id:str; account_id:str; voting:bool
@dataclass(frozen=True)
class CommitteeVote:
 id:str; committee_id:str; review_id:str; voter_account_id:str; recommendation:str; note:str|None; voted_at:datetime
@dataclass(frozen=True)
class AdmissionEvent:
 id:str; review_id:str; actor_id:str; event_type:str; from_state:str|None; to_state:str|None; note:str|None; created_at:datetime
