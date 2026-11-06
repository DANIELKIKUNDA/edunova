from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class AssignmentState(StrEnum):DRAFT='draft';SCHEDULED='scheduled';PUBLISHED='published';CLOSED='closed';GRADING='grading';RESULTS_PUBLISHED='results_published';ARCHIVED='archived'
class SubmissionState(StrEnum):DRAFT='draft';SUBMITTED='submitted';LATE='late';RETURNED='returned';GRADED='graded'
class AssignmentKind(StrEnum):INDIVIDUAL='individual';GROUP='group'
class QuestionKind(StrEnum):MCQ='mcq';TRUE_FALSE='true_false';NUMERIC='numeric';SYMBOLIC='symbolic';OPEN='open'
class ReviewState(StrEnum):NEEDS_REVIEW='needs_review';CLEARED='cleared';ESCALATED='escalated'
@dataclass(frozen=True,slots=True)
class Assignment:
 id:str;institution_id:str;offering_id:str;title:str;instructions:str;kind:AssignmentKind;opens_at:datetime|None;due_at:datetime;closes_at:datetime|None;max_attempts:int;max_score:float;state:AssignmentState;row_version:int;created_by:str;created_at:datetime;updated_at:datetime
@dataclass(frozen=True,slots=True)
class RubricCriterion:
 id:str;institution_id:str;assignment_id:str;position:int;label:str;description:str;max_points:float;created_at:datetime
@dataclass(frozen=True,slots=True)
class Submission:
 id:str;institution_id:str;assignment_id:str;student_account_id:str;group_key:str|None;attempt_no:int;text_content:str;attachment_refs:tuple[str,...];state:SubmissionState;submitted_at:datetime|None;row_version:int;created_at:datetime;updated_at:datetime
@dataclass(frozen=True,slots=True)
class GradingDecision:
 id:str;institution_id:str;submission_id:str;proposed_score:float|None;final_score:float|None;feedback:str;criterion_scores:tuple[str,...];confidence:float|None;proposal_source:str;validated_by:str|None;created_at:datetime;updated_at:datetime
@dataclass(frozen=True,slots=True)
class SimilarityFlag:
 id:str;institution_id:str;assignment_id:str;submission_a_id:str;submission_b_id:str;score:float;review_state:str;created_at:datetime

@dataclass(frozen=True,slots=True)
class AssignmentGroup:
 id:str;institution_id:str;assignment_id:str;group_key:str;member_account_ids:tuple[str,...];locked:bool;created_at:datetime
@dataclass(frozen=True,slots=True)
class AutoGradeItem:
 id:str;institution_id:str;assignment_id:str;kind:QuestionKind;prompt:str;expected_answer:str;points:float;tolerance:float|None;created_at:datetime
@dataclass(frozen=True,slots=True)
class ReopenGrant:
 id:str;institution_id:str;assignment_id:str;student_account_id:str|None;group_key:str|None;until:datetime;reason:str;granted_by:str;created_at:datetime
@dataclass(frozen=True,slots=True)
class StudentResult:
 assignment_id:str;submission_id:str;final_score:float;max_score:float;feedback:str;published:bool
