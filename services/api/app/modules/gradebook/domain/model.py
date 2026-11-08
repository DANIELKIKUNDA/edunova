from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class GradebookState(StrEnum): DRAFT='draft'; OPEN='open'; LOCKED='locked'; PUBLISHED='published'; ARCHIVED='archived'
class ComponentKind(StrEnum): ASSIGNMENT='assignment'; TEST='test'; EXAM='exam'; PRACTICAL='practical'; ORAL='oral'; OTHER='other'
class MarkState(StrEnum): DRAFT='draft'; VALIDATED='validated'; VOID='void'
class AttendanceOutcome(StrEnum): PRESENT='present'; ABSENT='absent'; JUSTIFIED_ABSENCE='justified_absence'; EXEMPT='exempt'
class ExamSessionKind(StrEnum): REGULAR='regular'; MAKEUP='makeup'; SPECIAL='special'
class ExamSessionState(StrEnum): DRAFT='draft'; SCHEDULED='scheduled'; CLOSED='closed'; CANCELLED='cancelled'
@dataclass(frozen=True,slots=True)
class Gradebook:
 id:str;institution_id:str;offering_id:str;title:str;state:GradebookState;pass_percent:float;row_version:int;created_by:str;created_at:datetime;updated_at:datetime
@dataclass(frozen=True,slots=True)
class GradeComponent:
 id:str;institution_id:str;gradebook_id:str;title:str;kind:ComponentKind;weight_percent:float;max_score:float;source_assignment_id:str|None;position:int;created_at:datetime
@dataclass(frozen=True,slots=True)
class StudentMark:
 id:str;institution_id:str;gradebook_id:str;component_id:str;student_account_id:str;score:float|None;state:MarkState;source_ref:str|None;validated_by:str|None;row_version:int;created_at:datetime;updated_at:datetime;attendance:AttendanceOutcome=AttendanceOutcome.PRESENT;note:str|None=None
@dataclass(frozen=True,slots=True)
class ExamSession:
 id:str;institution_id:str;gradebook_id:str;component_id:str;kind:ExamSessionKind;state:ExamSessionState;starts_at:datetime;ends_at:datetime;room:str|None;instructions:str|None;row_version:int;created_by:str;created_at:datetime;updated_at:datetime
@dataclass(frozen=True,slots=True)
class AcademicResult:
 gradebook_id:str;student_account_id:str;percent:float;passed:bool;complete:bool;components:tuple[str,...];published:bool
