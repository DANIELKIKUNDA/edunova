from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class MisconceptionState(StrEnum): OPEN="open"; IMPROVING="improving"; RESOLVED="resolved"; RELAPSED="relapsed"
class RemediationStepType(StrEnum): DIAGNOSE="diagnose"; EXPLAIN="explain"; WORKED_EXAMPLE="worked_example"; PRACTICE="practice"; TRANSFER="transfer"; REASSESS="reassess"; SPACED_REVIEW="spaced_review"
class RootCause(StrEnum): KNOWLEDGE_GAP="knowledge_gap"; MISCONCEPTION="misconception"; PROCEDURAL="procedural"; TRANSFER="transfer"; RETRIEVAL="retrieval"; CARELESSNESS="carelessness"; INSUFFICIENT_EVIDENCE="insufficient_evidence"
class TutorIntervention(StrEnum): RETRIEVAL="retrieval"; CONCEPT_REBUILD="concept_rebuild"; CONTRAST_CASES="contrast_cases"; WORKED_EXAMPLE="worked_example"; FADING="fading"; TRANSFER="transfer"; REFLECTION="reflection"
class RemediationEventType(StrEnum): DIAGNOSED="diagnosed"; PATH_CREATED="path_created"; PRACTICE_RECORDED="practice_recorded"; VERIFIED="verified"; RETENTION_CHECKED="retention_checked"; RELAPSED="relapsed"
@dataclass(frozen=True)
class Misconception:
 id:str; account_id:str; course_id:str; chapter_id:str|None; concept_id:str; label:str; evidence:tuple[str,...]; bloom_gap:str; severity:int; confidence:int; state:MisconceptionState; created_at:datetime; updated_at:datetime; row_version:int=1; root_cause:RootCause=RootCause.INSUFFICIENT_EVIDENCE; hypothesis:str=""; counter_evidence:tuple[str,...]=(); relapse_count:int=0
@dataclass(frozen=True)
class RemediationStep:
 order:int; kind:RemediationStepType; title:str; instruction:str; minutes:int; bloom_target:str; success_criterion:str; intervention:TutorIntervention=TutorIntervention.CONCEPT_REBUILD; hint_policy:str="progressive"; source_required:bool=True
@dataclass(frozen=True)
class RemediationPath:
 id:str; account_id:str; misconception_id:str; course_id:str; chapter_id:str|None; steps:tuple[RemediationStep,...]; current_step:int; status:str; baseline_score:int|None; verification_score:int|None; created_at:datetime; updated_at:datetime; row_version:int=1; model_version:str="remediation-v2"; difficulty_level:int=2; consecutive_successes:int=0; consecutive_failures:int=0; last_transfer_score:int|None=None; next_review_at:datetime|None=None; last_mutation_id:str|None=None; total_practice_attempts:int=0; successful_practice_attempts:int=0; cumulative_gain:int=0
@dataclass(frozen=True)
class DiagnosticSignal:
 course_id:str; chapter_id:str|None; concept_id:str; label:str; bloom_gap:str; score:int; evidence:tuple[str,...]; confidence:int
@dataclass(frozen=True)
class VerificationResult:
 path_id:str; baseline_score:int; verification_score:int; gain:int; resolved:bool; next_action:str; transfer_verified:bool=False; retention_due:bool=False
@dataclass(frozen=True)
class TutorDecision:
 intervention:TutorIntervention; difficulty_level:int; bloom_target:str; rationale:tuple[str,...]; max_hints:int; require_transfer:bool=True

@dataclass(frozen=True)
class RemediationEvent:
 id:str; account_id:str; path_id:str|None; misconception_id:str|None; kind:RemediationEventType; occurred_at:datetime; payload:dict; mutation_id:str|None=None
@dataclass(frozen=True)
class InterventionOutcome:
 intervention:TutorIntervention; attempts:int; successes:int; avg_gain:float
