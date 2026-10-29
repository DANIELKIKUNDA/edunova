from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

class PlanItemState(StrEnum): PLANNED='planned'; DONE='done'; SKIPPED='skipped'; SUPERSEDED='superseded'
class PlanSource(StrEnum): ADAPTIVE='adaptive'; EXAM='exam'; REVIEW='review'; ERROR='error'; MANUAL='manual'

@dataclass(frozen=True)
class PlannerPreferences:
    account_id:str; timezone:str='Africa/Lubumbashi'; daily_limit_minutes:int=120; session_max_minutes:int=45
    preferred_start_hour:int=18; preferred_end_hour:int=22; buffer_minutes:int=10; weekend_enabled:bool=True; row_version:int=1

@dataclass(frozen=True)
class BusyBlock:
    id:str; account_id:str; starts_at:datetime; ends_at:datetime; label:str; source:str='manual'

@dataclass(frozen=True)
class StudyPlanItem:
    id:str; account_id:str; plan_date:date; starts_at:datetime; ends_at:datetime; course_id:str; chapter_id:str|None
    action:str; label:str; source:PlanSource; priority:int; reason:str; expected_outcome:str; state:PlanItemState=PlanItemState.PLANNED
    row_version:int=1
    @property
    def minutes(self): return max(0,int((self.ends_at-self.starts_at).total_seconds()//60))

@dataclass(frozen=True)
class DailyPlan:
    plan_date:date; items:tuple[StudyPlanItem,...]; planned_minutes:int; capacity_minutes:int; overflow_minutes:int
    explanation:tuple[str,...]; generated_at:datetime; model_version:str='planner-v2'
