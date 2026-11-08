from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class JuryState(StrEnum):
    DRAFT = 'draft'
    LOCKED = 'locked'
    PUBLISHED = 'published'

class JuryDecision(StrEnum):
    PASS = 'pass'
    RETAKE = 'retake'
    DEFERRED = 'deferred'

@dataclass(frozen=True)
class JurySession:
    id: str
    institution_id: str
    cohort_id: str
    curriculum_id: str
    academic_year_id: str
    name: str
    min_credits: float
    state: JuryState
    row_version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    quorum: int = 1

@dataclass(frozen=True)
class JuryOutcome:
    id: str
    session_id: str
    student_id: str
    decision: JuryDecision
    credits_earned: float
    credits_required: float
    evidence_hash: str
    decided_by: str
    reason: str
    created_at: datetime

class JuryMemberRole(StrEnum):
    PRESIDENT = "president"
    SECRETARY = "secretary"
    MEMBER = "member"

class JuryVoteChoice(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"

@dataclass(frozen=True)
class JuryMember:
    id: str
    session_id: str
    account_id: str
    role: JuryMemberRole
    voting: bool
    created_at: datetime

@dataclass(frozen=True)
class JuryVote:
    id: str
    session_id: str
    student_id: str
    account_id: str
    choice: JuryVoteChoice
    rationale: str
    created_at: datetime

@dataclass(frozen=True)
class JuryMinutes:
    id: str
    session_id: str
    content_hash: str
    outcome_count: int
    generated_by: str
    generated_at: datetime
