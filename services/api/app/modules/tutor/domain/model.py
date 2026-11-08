from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class TutorMove(StrEnum):
    EXPLAIN='explain'; SOCRATIC='socratic'; HINT='hint'; CHECK='check'; PRACTICE='practice'; PREREQUISITE='prerequisite'; REMEDIATE='remediate'; ABSTAIN='abstain'
class TutorSessionState(StrEnum): ACTIVE='active'; PAUSED='paused'; CLOSED='closed'
@dataclass(frozen=True,slots=True)
class TutorEvidence:
    concept_id:str; mastery:float=0.5; error_count:int=0; bloom_level:str='understand'
@dataclass(frozen=True,slots=True)
class TutorSession:
    id:str; account_id:str; course_id:str|None; target_concept_id:str|None; subject_domain:str; high_stakes:bool; state:TutorSessionState; hint_level:int; turn_count:int; row_version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True,slots=True)
class TutorDecision:
    move:TutorMove; reason:str; target_concept_id:str|None; bloom_target:str; hint_level:int; requires_sources:bool; next_action:str
@dataclass(frozen=True,slots=True)
class TutorTurn:
    id:str; session_id:str; account_id:str; question:str; decision:TutorDecision; evidence:tuple[str,...]; created_at:datetime; mutation_id:str|None=None
