from dataclasses import dataclass
from enum import StrEnum

class RiskBand(StrEnum): LOW='low'; WATCH='watch'; HIGH='high'; CRITICAL='critical'
class ConfidenceBand(StrEnum): LOW='low'; MEDIUM='medium'; HIGH='high'

@dataclass(frozen=True)
class AdaptiveDecision:
    action:str; priority:int; course_id:str; chapter_id:str|None; reason:str; evidence:tuple[str,...]; minutes:int; confidence:float
    urgency:str='normal'; expected_outcome:str='Consolider les acquis'; due_reason:str|None=None

@dataclass(frozen=True)
class KnowledgeGap:
    course_id:str; chapter_id:str; severity:int; label:str; evidence:tuple[str,...]; suggested_action:str

@dataclass(frozen=True)
class ExamReadiness:
    plan_id:str; title:str; exam_at:str; days_remaining:int; readiness:float; daily_minutes:int; at_risk_courses:tuple[str,...]

@dataclass(frozen=True)
class IntelligenceProfile:
    mastery:float; readiness:float; consistency:float; risk:RiskBand; evidence_count:int; decisions:tuple[AdaptiveDecision,...]
    confidence:ConfidenceBand=ConfidenceBand.LOW; gaps:tuple[KnowledgeGap,...]=(); exam_readiness:tuple[ExamReadiness,...]=(); model_version:str='adaptive-v2'

def risk_for(score,evidence):
    if evidence<2:return RiskBand.WATCH
    if score<35:return RiskBand.CRITICAL
    if score<55:return RiskBand.HIGH
    if score<72:return RiskBand.WATCH
    return RiskBand.LOW

def confidence_for(evidence, assessed):
    if evidence>=8 and assessed>=3:return ConfidenceBand.HIGH
    if evidence>=3 and assessed>=1:return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW
