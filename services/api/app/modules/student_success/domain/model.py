from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class SuccessCase:
 id:str
 institution_id:str
 student_id:str
 category:str
 severity:str
 description:str
 state:str
 assigned_to:str|None
 created_by:str
 created_at:datetime
 updated_at:datetime
 version:int
 source_kind:str|None=None
 source_key:str|None=None
 evidence_hash:str|None=None

@dataclass(frozen=True)
class SuccessEvent:
 id:str
 case_id:str
 actor_id:str
 action:str
 note:str
 created_at:datetime

@dataclass(frozen=True)
class SuccessPlan:
 id:str
 case_id:str
 institution_id:str
 student_id:str
 objective:str
 state:str
 target_date:str|None
 created_by:str
 created_at:datetime
 updated_at:datetime
 version:int

@dataclass(frozen=True)
class SuccessAction:
 id:str
 plan_id:str
 title:str
 assigned_to:str
 due_date:str|None
 state:str
 completion_note:str|None
 created_at:datetime
 completed_at:datetime|None
 version:int

@dataclass(frozen=True)
class SuccessAssessment:
 id:str
 plan_id:str
 case_id:str
 institution_id:str
 student_id:str
 failed_results:int
 published_results:int
 attendance_records:int
 attendance_rate:float|None
 outcome:str
 evidence_hash:str
 assessed_by:str
 created_at:datetime
