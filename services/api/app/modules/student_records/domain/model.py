from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class StudentState(StrEnum): ACTIVE='active'; SUSPENDED='suspended'; WITHDRAWN='withdrawn'; GRADUATED='graduated'; ARCHIVED='archived'
class RegistrationState(StrEnum): ENROLLED='enrolled'; SUSPENDED='suspended'; WITHDRAWN='withdrawn'; COMPLETED='completed'; CANCELLED='cancelled'
class StudentAdministrativeAction(StrEnum): IDENTITY_CORRECTION='identity_correction'; LEAVE_STARTED='leave_started'; LEAVE_ENDED='leave_ended'; REGISTRATION_STATE_CHANGED='registration_state_changed'
@dataclass(frozen=True)
class StudentRecord:
 id:str; institution_id:str; account_id:str; matricule:str; admission_review_id:str; application_id:str; program_unit_id:str; curriculum_id:str; cohort_id:str; given_names:str; family_name:str; birth_date:str|None; nationality_code:str|None; email:str|None; phone_number:str|None; state:StudentState; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class AcademicRegistration:
 id:str; student_id:str; institution_id:str; academic_year_id:str; cohort_id:str; curriculum_id:str; state:RegistrationState; registered_by:str; registered_at:datetime; row_version:int
@dataclass(frozen=True)
class StudentEvent:
 id:str; student_id:str; actor_id:str; event_type:str; from_state:str|None; to_state:str|None; note:str|None; created_at:datetime
class CourseRegistrationState(StrEnum): ENROLLED='enrolled'; VALIDATED='validated'; FAILED='failed'; EXEMPTED='exempted'; WITHDRAWN='withdrawn'
@dataclass(frozen=True)
class StudentCourseRegistration:
 id:str; registration_id:str; student_id:str; curriculum_course_id:str; semester:int; course_code:str|None; course_title:str; credits:float|None; state:CourseRegistrationState; created_at:datetime

@dataclass(frozen=True)
class StudentAdministrativeHistory:
 id:str; student_id:str; institution_id:str; actor_id:str; action_type:str; reason:str; before_json:str|None; after_json:str|None; created_at:datetime
