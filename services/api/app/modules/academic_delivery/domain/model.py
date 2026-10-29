from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class OfferingCurriculumLink:
    id: str
    institution_id: str
    offering_id: str
    curriculum_id: str
    curriculum_course_id: str
    cohort_id: str
    bound_by: str
    bound_at: datetime


@dataclass(frozen=True, slots=True)
class PublishedCourseResult:
    id: str
    institution_id: str
    student_id: str
    student_account_id: str
    course_registration_id: str
    curriculum_course_id: str
    offering_id: str
    gradebook_id: str
    percent: float
    passed: bool
    evidence_hash: str
    published_by: str
    published_at: datetime
